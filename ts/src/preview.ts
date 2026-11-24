// What the model sees of the data: plotkit.charts.preview (per sheet, the columns with their type and values) and
// plotkit.agent.preview (the Korean text of the first message, "데이터 미리보기: ...").
import type { InputFile } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import { formatValue, PyInt, pyRepr } from "./pyfmt.ts";
import { frameFromRows } from "./frame.ts";
import {
  cmpCodePoints, findFile, intStr, isoFromMs, normPath, pathName, pathParent, readTables, selectSheets,
  type ReadOptions,
} from "./reader.ts";

type Num = number | PyInt;

export interface PreviewColumn {
  col: string | null;
  name: string;
  type: "number" | "date" | "text";
  min?: number | string | null;
  max?: number | string | null;
  values?: (number | string)[];
  n_values?: number;
}

export interface PreviewSheet {
  sheet: string;
  rows?: number;
  header_row?: number | null;
  columns?: PreviewColumn[];
  error?: string;
}

export interface Preview {
  ok: true;
  file: string;
  sheets: PreviewSheet[];
}

/** _r: a value for the preview, an int when it is whole, else 6 significant digits. */
function r(v: number): Num {
  if (Number.isInteger(v)) return new PyInt(v);
  if (!Number.isFinite(v)) return v;
  return parseFloat(formatValue(v, ".6g"));
}

const plain = (v: unknown): any => (v instanceof PyInt ? v.value : Array.isArray(v) ? v.map(plain) : v);

/** str() of a preview number. */
function numText(v: Num | null | undefined): string {
  if (v === null || v === undefined) return "None";
  return v instanceof PyInt ? intStr(v.value) : pyRepr(v);
}

interface RawColumn { col: string | null; name: string; type: "number" | "date" | "text"; min?: Num | string | null; max?: Num | string | null; values?: (Num | string)[]; n_values?: number }
interface RawSheet { sheet: string; rows?: number; header_row?: number | null; columns?: RawColumn[]; error?: string }

async function previewRaw(file: InputFile, sheets: unknown, read: ReadOptions | null, maxValues: number): Promise<RawSheet[]> {
  const tables = await readTables(file, read ?? {});
  const names = [...tables.sheets.keys()];
  const out: RawSheet[] = [];
  for (const n of sheets === "all" || sheets === null || sheets === undefined ? names : selectSheets(names, sheets, file.name)) {
    let df;
    try {
      df = frameFromRows(tables.sheets.get(n)!, tables.decimal);
    } catch (e) {
      if (!(e instanceof PlotkitError)) throw e;
      out.push({ sheet: n, error: e.message });
      continue;
    }
    const cols: RawColumn[] = [];
    df.columns.forEach((c, i) => {
      const s = df.data[i];
      const e: RawColumn = { col: Object.hasOwn(df.letters, c) ? df.letters[c] : null, name: c, type: "text" };
      if (df.dtypes[i] === "float") {
        const v = (s as number[]).filter(x => !Number.isNaN(x));
        let min = Infinity, max = -Infinity;
        for (const x of v) { if (x < min) min = x; if (x > max) max = x; }
        Object.assign(e, { type: "number", min: v.length ? r(min) : null, max: v.length ? r(max) : null });
        const uniq = [...new Set(v.map(x => (x === 0 ? 0 : x)))];
        if (uniq.length > 0 && uniq.length <= 8) e.values = uniq.sort((a, b) => a - b).map(r);
      } else if (df.dtypes[i] === "datetime") {
        const v = (s as number[]).filter(x => !Number.isNaN(x));
        let min = Infinity, max = -Infinity;
        for (const x of v) { if (x < min) min = x; if (x > max) max = x; }
        Object.assign(e, { type: "date", min: v.length ? isoFromMs(min).slice(0, 10) : null, max: v.length ? isoFromMs(max).slice(0, 10) : null });
      } else {
        const u = [...new Set(s.filter(x => x !== null && !(typeof x === "number" && Number.isNaN(x))))] as string[];
        Object.assign(e, { type: "text", n_values: u.length, values: [...u.slice(0, maxValues), ...(u.length > maxValues ? ["…"] : [])] });
      }
      cols.push(e);
    });
    out.push({ sheet: n, rows: df.data[0]?.length ?? 0, header_row: df.headerRow, columns: cols });
  }
  return out;
}

/** charts.preview: per sheet, the rows, the header row and every column with its letter, type and range or values.
 *  name: the file name to report (default: file.name). */
export async function preview(file: InputFile, sheets: unknown = "all", read: ReadOptions | null = null, maxValues = 12, name?: string): Promise<Preview> {
  const raw = await previewRaw(file, sheets, read, maxValues);
  const out: PreviewSheet[] = raw.map(sh => sh.columns ? {
    ...sh, columns: sh.columns.map(c => ({ ...c, ...("min" in c ? { min: plain(c.min), max: plain(c.max) } : {}), ...(c.values ? { values: plain(c.values) } : {}) })),
  } as PreviewSheet : sh as PreviewSheet);
  return { ok: true, file: name ?? file.name, sheets: out };
}

/** fnmatch of one path component (pathlib's glob: "*" and "?" do not cross "/", hidden files match). */
function globRegex(pat: string): RegExp {
  let re = "";
  for (let i = 0; i < pat.length; i++) {
    const ch = pat[i];
    if (ch === "*") re += "[^/]*";
    else if (ch === "?") re += "[^/]";
    else if (ch === "[") {
      let j = i + 1;
      if (pat[j] === "!") j++;
      if (pat[j] === "]") j++;
      while (j < pat.length && pat[j] !== "]") j++;
      if (j >= pat.length) re += "\\[";
      else {
        let body = pat.slice(i + 1, j).replace(/\\/g, "\\\\");
        if (body.startsWith("!")) body = "^" + body.slice(1);
        else if (body.startsWith("^")) body = "\\" + body;
        re += `[${body}]`;
        i = j;
      }
    } else re += ch.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  }
  return new RegExp(`^${re}$`, "su");
}

function cmpPaths(a: string, b: string): number {
  const x = a.split("/"), y = b.split("/");
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const d = cmpCodePoints(x[i], y[i]);
    if (d) return d;
  }
  return x.length - y.length;
}

/** agent.preview: the data preview the model sees instead of the files, per file and sheet ("데이터 미리보기: ...").
 *  names: the files as the user named them (glob patterns with * or ? match the given files' names). */
export async function previewText(names: string[], files: InputFile[]): Promise<string> {
  const parts: string[] = [];
  for (const f of names) {
    const p = normPath(String(f));
    let paths: string[];
    if (/[*?]/.test(String(f))) {
      const parent = pathParent(p), re = globRegex(pathName(p));
      const hits = new Set<string>();
      for (const file of files) {
        const q = normPath(file.name);
        if (pathParent(q) === parent && re.test(pathName(q))) hits.add(q);
      }
      paths = [...hits].sort(cmpPaths);
    } else paths = [p];
    const lines: string[] = [];
    for (const path of paths) {
      let sheets: RawSheet[];
      try {
        sheets = await previewRaw(findFile(files, path), "all", null, 12);
      } catch (e) {
        lines.push(`파일 ${path}: 읽기 실패 (${e instanceof Error ? e.message : String(e)})`);
        continue;
      }
      lines.push(`파일 ${path}` + (sheets.length > 1 ? ` (시트 ${sheets.length}개)` : ""));
      for (const sh of sheets.slice(0, 12)) {
        if (sh.error !== undefined) {
          lines.push(`  시트 '${sh.sheet}': ${sh.error}`);
          continue;
        }
        const cols = sh.columns!.map(c => {
          if (c.type === "number") {
            return `${c.col} ${c.name} [수치 ${numText(c.min as Num)}~${numText(c.max as Num)}`
              + (c.values?.length ? `; 값 [${(c.values as Num[]).map(numText).join(", ")}]` : "") + "]";
          }
          if (c.type === "date") return `${c.col} ${c.name} [날짜 ${c.min ?? "None"}~${c.max ?? "None"}]`;
          return `${c.col} ${c.name} [텍스트 ${c.n_values}종: ${(c.values as string[]).join(", ")}]`;
        });
        lines.push(`  시트 '${sh.sheet}' (${sh.rows}행): ` + cols.join(" | "));
      }
      if (sheets.length > 12) lines.push(`  … 시트 ${sheets.length - 12}개 더: ` + sheets.slice(12).map(s => s.sheet).join(", "));
    }
    parts.push(lines.join("\n"));
  }
  return "데이터 미리보기:\n" + parts.join("\n");
}
