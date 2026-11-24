import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, diff, BASES } from "./golden.ts";
import { decodeText, isoFromMs, loadSheets, readTables, selectSheets } from "../src/reader.ts";
import { loadFrame, toDate } from "../src/frame.ts";
import { preview, previewText } from "../src/preview.ts";
import { PlotkitError } from "../src/errors.ts";
import type { Cell, InputFile } from "../src/types.ts";

const CASES = golden("reader");

// Expected differences: old binary .xls files are read by xlrd in Python; ExcelJS can not read them, so the port
// refuses them with a PlotkitError that asks for .xlsx (the preview text then says the file could not be read).
const XLS_REFUSED = new Set(["tests/inputs|old_format.xls"]);

const plainCell = (c: Cell) => (c !== null && typeof c === "object" ? { $date: c.date } : c);

function fileOf(c: { base: string; name: string }): InputFile {
  return { name: c.name, bytes: new Uint8Array(readFileSync(join(BASES[c.base], c.name))) };
}

test("there are reader cases", () => {
  assert.ok(CASES.length >= 44, `${CASES.length} cases`);
});

for (const c of CASES) {
  const key = `${c.base}|${c.name}`;
  test(`reader: ${key}`, async () => {
    const files = [fileOf(c)];
    if (XLS_REFUSED.has(key)) {
      await assert.rejects(readTables(files[0]), (e: unknown) => e instanceof PlotkitError && /\.xls/.test(e.message) && /save it as \.xlsx/.test(e.hint));
      await assert.rejects(preview(files[0]), PlotkitError);
      const text = await previewText([c.name], files);
      assert.match(text, new RegExp(`^데이터 미리보기:\\n파일 ${c.name.replace(/\./g, "\\.")}: 읽기 실패 \\(.*\\.xls`));
      return;
    }
    // read_tables
    if (c.tables_error) {
      await assert.rejects(readTables(files[0]), (e: unknown) =>
        e instanceof PlotkitError && e.message === c.tables_error.error && e.hint === c.tables_error.hint);
    } else {
      const t = await readTables(files[0]);
      const tables = Object.fromEntries([...t.sheets].map(([k, rows]) => [k, rows.map(r => r.map(plainCell))]));
      assert.deepEqual(Object.keys(tables), Object.keys(c.tables), "sheet names and order");
      assert.deepEqual(diff(tables, c.tables), []);
      assert.equal(t.decimal, c.decimal);
    }
    // charts.preview
    if (c.preview_error) {
      await assert.rejects(preview(files[0]), (e: unknown) =>
        e instanceof PlotkitError && e.message === c.preview_error.error && e.hint === c.preview_error.hint);
    } else {
      assert.deepEqual(diff(await preview(files[0]), c.preview), []);
    }
    // agent.preview
    assert.equal(await previewText([c.name], files), c.preview_text);
  });
}

test("preview text: glob patterns expand to the given files, sorted; missing files are reported", async () => {
  const raman = CASES.filter(c => c.base === "eval/cnt" && c.name.startsWith("data/raman/"));
  const files = raman.map(fileOf).reverse();
  const text = await previewText(["data/raman/R*-26071?-1.csv", "nope.csv"], files);
  const want = raman.filter(c => /R.*-26071.-1\.csv$/.test(c.name)).map(c => c.preview_text.replace(/^데이터 미리보기:\n/, ""));
  assert.equal(text, "데이터 미리보기:\n" + want.join("\n") + "\n파일 nope.csv: 읽기 실패 (file not found: nope.csv)");
});

test("cp949 text with UHC-extension Hangul decodes as Python's cp949 codec does", async () => {
  const bytes = new Uint8Array([191, 194, 181, 181, 44, 140, 99, 176, 170, 10]);   // "온도,똠값\n".encode("cp949")
  assert.equal(decodeText(bytes), "온도,똠값\n");
  assert.equal(decodeText(new Uint8Array([0x41, 0xc9, 0xa1, 0xa1])), "AÉ¡¡");          // not UTF-8, user-defined row of cp949 -> latin-1
});

// ------------------------------------------------------------------- the reader fixes (tests/test_reader_fixes.py)
const enc = new TextEncoder();
const file = (name: string, data: string | Uint8Array): InputFile => ({ name, bytes: typeof data === "string" ? enc.encode(data) : data });
const TGA = fileOf({ base: "tests/inputs", name: "TGA.xlsx" });
const TGA_SHEETS = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"];
const TGA_REPR = "['1006R1-V normal', '1006R1-V acid', '1006R1-V 750C']";
const CSV = "t,v\n" + Array.from({ length: 12 }, (_, i) => `${30 + 10 * i},${100 - i}`).join("\n") + "\n";

function err(fn: () => unknown): [string, string] {
  try {
    fn();
  } catch (e) {
    if (e instanceof PlotkitError) return [e.message, e.hint];
    throw e;
  }
  throw new Error("no error");
}
async function aerr(p: Promise<unknown>): Promise<[string, string]> {
  try {
    await p;
  } catch (e) {
    if (e instanceof PlotkitError) return [e.message, e.hint];
    throw e;
  }
  throw new Error("no error");
}

test("fixes: sheet names of other digits are names; sheet numbers", async () => {
  for (const sel of ["²", "٣", "1²"]) {
    assert.deepEqual(err(() => selectSheets(TGA_SHEETS, sel, "dir/TGA.xlsx")), [`sheet "${sel}" not found in TGA.xlsx`, `sheet names: ${TGA_REPR}`]);
  }
  assert.deepEqual(selectSheets(TGA_SHEETS, " 2 ", "TGA.xlsx"), ["1006R1-V acid"]);
  assert.deepEqual(selectSheets(TGA_SHEETS, [3, "1", 2.7], "TGA.xlsx"), ["1006R1-V 750C", "1006R1-V normal", "1006R1-V acid"]);
  for (const [bad, shown] of [[NaN, "nan"], [Infinity, "inf"], [4, "4"], ["0", "0"]] as [unknown, string][]) {
    assert.deepEqual(err(() => selectSheets(TGA_SHEETS, bad, "TGA.xlsx")), [`sheet number ${shown} does not exist in TGA.xlsx`, `it has 3 sheet(s): ${TGA_REPR}`]);
  }
  assert.deepEqual(await aerr(loadSheets({ file: ["TGA.xlsx"], sheets: "²", read: {} }, [TGA])), ['sheet "²" not found in TGA.xlsx', `sheet names: ${TGA_REPR}`]);
  assert.deepEqual(await aerr(loadFrame({ file: ["TGA.xlsx"], sheets: [], read: {} }, [TGA])), ["no sheet to read", 'set "sheets" to a sheet name, a number from 1, or "all"']);
});

const MIXED_DATES = ["2026-03-01 08:00", "2026-03-02", "2026-03-03T09:30:15", "2026/03/04", "2026.3.5 7:05", "2026-02-30",
  "2026-03-07 23:59:59", "2026-3-8", "2026-03-09 12:00", "n/a"];
const MIXED_WANT = ["2026-03-01T08:00:00", "2026-03-02T00:00:00", "2026-03-03T09:30:15", "2026-03-04T00:00:00", "2026-03-05T07:05:00", null,
  "2026-03-07T23:59:59", "2026-03-08T00:00:00", "2026-03-09T12:00:00", null];
const isoOf = (v: unknown) => (typeof v === "number" && !Number.isNaN(v) ? isoFromMs(v) : null);

test("fixes: a date column may mix date forms; one form reads as before", async () => {
  const f = file("mixed.csv", "d,v\n" + MIXED_DATES.map((d, i) => `${d},${i}`).join("\n") + "\n");
  const df = await loadFrame({ file: ["mixed.csv"], sheets: null, read: {} }, [f]);
  assert.equal(df.dtypes[0], "datetime");
  assert.deepEqual(df.data[0].map(isoOf), MIXED_WANT);
  const pv = (await preview(f)).sheets[0].columns![0];
  assert.deepEqual([pv.type, pv.min, pv.max], ["date", "2026-03-01", "2026-03-09"]);
  const days = Array.from({ length: 10 }, (_, d) => `2026-04-${String(d + 1).padStart(2, "0")}`);
  const g = file("days.csv", "d,v\n" + days.map((d, i) => `${d},${i}`).join("\n") + "\nn/a,10\n");
  const dg = await loadFrame({ file: ["days.csv"], sheets: null, read: {} }, [g]);
  assert.deepEqual(dg.data[0].map(v => isoOf(v)?.slice(0, 10) ?? null), [...days, null]);
  assert.equal(isoFromMs(toDate(" 2026-01-02 03:04:05.5 ")), "2026-01-02T03:04:05.500000");
  assert.equal(isoFromMs(toDate({ date: "2026-01-02T03:00:00" })), "2026-01-02T03:00:00");
  for (const v of ["2026-13-01", "2026-01-01 24:00", "0000-01-01", "08:30", "2026-01", 45000, true, null]) assert.ok(Number.isNaN(toDate(v)), String(v));
});

const UHC = new Uint8Array([191, 194, 181, 181, 44, 140, 99, 176, 170, 10, 49, 44, 50, 10, 51, 44, 52, 10]);   // "온도,똠값\n1,2\n3,4\n" in cp949
const ENC_HINT = 'check read.encoding (e.g. "utf-8" or "cp949"), or leave it out to detect the encoding';

test("fixes: encodings", async () => {
  const f = file("k.csv", UHC);
  assert.deepEqual((await readTables(f)).sheets.get("k")![0], ["온도", "똠값"]);
  assert.deepEqual((await readTables(f, { encoding: "cp949" })).sheets.get("k")![0], ["온도", "똠값"]);
  assert.deepEqual(await aerr(readTables(f, { encoding: "utf-8" })), ["k.csv is not utf-8 text", ENC_HINT]);
  assert.deepEqual(await aerr(readTables(f, { encoding: "EUC_KR" })), ["k.csv is not EUC_KR text", ENC_HINT]);
  assert.deepEqual(await aerr(readTables(f, { encoding: "klingon" })), ['unknown encoding "klingon"', 'use "utf-8", "cp949", "utf-16" or "latin-1", or leave read.encoding out']);
  const g = file("ks.csv", new Uint8Array([191, 194, 181, 181, 44, 176, 170, 10, 49, 44, 50, 10]));                  // "온도,값\n1,2\n" in euc-kr
  assert.deepEqual((await readTables(g, { encoding: "euc-kr" })).sheets.get("ks")![0], ["온도", "값"]);
  const hint = "set read.encoding, or save the file again as UTF-8";
  const u16 = new Uint8Array([0xff, 0xfe, 0x61, 0, 0x09, 0, 0x62, 0, 0x0a, 0, 0]);                                     // odd length
  assert.deepEqual(await aerr(readTables(file("u16.txt", u16))), ["u16.txt looks like UTF-16 text but could not be decoded", hint]);
  const u8 = new Uint8Array([0xef, 0xbb, 0xbf, ...enc.encode("a,b\n"), 0xff, 0xfe, ...enc.encode("1,2\n")]);
  assert.deepEqual(await aerr(readTables(file("u8.txt", u8))), ["u8.txt looks like UTF-8 text but could not be decoded", hint]);
});

test("fixes: bad separators", async () => {
  for (const [sep, shown] of [["", "''"], [5, "5"], [["a"], "['a']"], [true, "True"]] as [unknown, string][]) {
    assert.deepEqual(await aerr(readTables(file("t.csv", CSV), { sep })), [`read.sep must be a separator like "," or "tab", not ${shown}`, 'use ",", ";", "tab" or "space", or leave it out']);
  }
});

test("fixes: row numbers", async () => {
  const f = file("t.csv", CSV);
  const cases: [string, unknown, string][] = [["header_row", "abc", "'abc'"], ["header_row", -2, "-2"], ["header_row", "0", "'0'"],
    ["data_start_row", true, "True"], ["data_start_row", "2.5", "'2.5'"], ["data_start_row", [3], "[3]"]];
  for (const [key, value, shown] of cases) {
    const want = [`t.csv / sheet "t": read.${key} must be a row number from 1, not ${shown}`, "rows count from 1 at the top of the sheet, e.g. 3"];
    assert.deepEqual(await aerr(loadSheets({ file: ["t.csv"], sheets: "all", read: { [key]: value } }, [f])), want);
    assert.deepEqual(await aerr(loadFrame({ file: ["t.csv"], sheets: null, read: { [key]: value } }, [f])), want);
  }
  const end = ['t.csv / sheet "t": read.header_row 99 is after the end of the sheet (it has 13 rows)', "check read.header_row"];
  assert.deepEqual(await aerr(loadSheets({ file: ["t.csv"], sheets: "all", read: { header_row: 99, data_start_row: 2 } }, [f])), end);
  assert.deepEqual(await aerr(loadFrame({ file: ["t.csv"], sheets: null, read: { header_row: 99 } }, [f])), end);
  const [[, , t]] = await loadSheets({ file: ["t.csv"], sheets: "all", read: { header_row: "1", data_start_row: " 2 " } }, [f]);
  assert.ok(!(t instanceof PlotkitError));
  assert.deepEqual([t.columns.map(c => c.name), t.data_start_row], [["t", "v"], 2]);
  const df = await loadFrame({ file: ["t.csv"], sheets: null, read: { header_row: "1" } }, [f]);
  assert.deepEqual([df.columns, df.data[0].length], [["t", "v"], 12]);
});

test("fixes: not an .xlsx", async () => {
  assert.deepEqual(await aerr(readTables(file("bad.xlsx", "this is not a workbook"))),
    ["bad.xlsx could not be read as an .xlsx file", "check that it is an Excel workbook; open it in Excel and save it again as .xlsx"]);
});
