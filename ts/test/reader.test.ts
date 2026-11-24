import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { golden, diff, BASES } from "./golden.ts";
import { decodeText, readTables } from "../src/reader.ts";
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
