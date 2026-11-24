// Port of the table reading in plotkit/charts.py: raw rows -> a typed table (pandas DataFrame semantics: float64
// columns with NaN, datetime64 as epoch ms read as UTC with NaN for NaT, object columns of text), load_frame (the
// table a chart spec asks for, several sheets/files stacked) and find_col.
import type { Cell, Dtype, Frame, InputFile } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import { getCloseMatches } from "./difflib.ts";
import {
  base, cellStr, colLetter, daysFromCivil, findFile, isoFromMs, msFromIso, norm, pathName, pathStem, pyInt, pyLen,
  pyStrip, pyStrOf, pyTruthy, readTables, selectSheets, toNum, type ReadOptions,
} from "./reader.ts";

/** A table as frame_from_rows makes it: the Frame and its attrs header_row (1-based, or null) and data_start_row. */
export interface LoadedFrame extends Frame {
  headerRow: number | null;
  dataStartRow: number;
}

type Value = number | string | boolean | null;
type CellKind = "empty" | "date" | "num" | "text";

export const DATE_RE = /^\p{Nd}{4}[-./]\p{Nd}{1,2}[-./]\p{Nd}{1,2}([ T]\p{Nd}{1,2}:\p{Nd}{2}(:\p{Nd}{2})?)?$/u;

const isDateCell = (c: Cell): c is { date: string } => c !== null && typeof c === "object";

export function cellKind(c: Cell, decimal: string): CellKind {
  if (c === null || (typeof c === "string" && !pyStrip(c))) return "empty";
  if (isDateCell(c)) return "date";
  if (toNum(c, decimal) !== null) return "num";
  if (typeof c === "string" && DATE_RE.test(pyStrip(c))) return "date";
  return "text";
}

/** frame_from_rows: raw rows -> typed columns (number, date or text) and the header found. */
export function frameFromRows(rowsIn: Cell[][], decimal = ".", headerRow: unknown = null, dataStartRow: unknown = null): LoadedFrame {
  let width = 0;
  for (const r of rowsIn) width = Math.max(width, r.length);
  const rows: Cell[][] = rowsIn.map(r => r.length < width ? [...r, ...new Array<Cell>(width - r.length).fill(null)] : [...r]);
  const kinds = rows.map(r => r.map(c => cellKind(c, decimal)));
  const filled = kinds.map(r => r.filter(k => k !== "empty").length);
  if (!rows.length || !filled.some(n => n > 0)) throw new PlotkitError("this sheet is empty");
  const look = Math.min(rows.length, 40);
  let h: number | null = null;
  if (pyTruthy(headerRow)) {
    h = pyInt(headerRow, "read.header_row") - 1;
  } else {
    for (let i = 0; i < look; i++) {
      if (filled[i] < 2 || kinds[i].some(k => k === "num" || k === "date")) continue;
      const nxt: number[] = [];
      for (let j = i + 1; j < Math.min(rows.length, i + 12); j++) if (filled[j]) nxt.push(filled[j]);
      if (nxt.length && filled[i] >= 0.6 * Math.max(...nxt)) {
        h = i;
        break;
      }
    }
  }
  let units: number | null = null;
  let ds: number;
  if (pyTruthy(dataStartRow)) {
    ds = pyInt(dataStartRow, "read.data_start_row") - 1;
  } else if (h === null) {
    ds = filled.findIndex(n => n > 0);
  } else {
    ds = h + 1;
    while (ds < rows.length && !filled.at(ds)) ds++;
    if (ds < rows.length && !kinds.at(ds)!.some(k => k === "num") && ds + 1 < rows.length
      && kinds.at(ds + 1)!.some(k => k === "num")
      && rows.at(ds)!.every(c => c === null || pyLen(cellStr(c)) <= 14)) {
      units = ds;                                              // a units row under the names
      ds++;
    }
  }
  const head = h === null ? null : rows.at(h);
  const unitRow = units === null ? null : rows.at(units)!;
  const body = rows.slice(ds).filter(r => r.some(c => c !== null && pyStrip(cellStr(c))));
  const columns: string[] = [], dtypes: Dtype[] = [], data: Value[][] = [], letters: Record<string, string> = {};
  for (let j = 0; j < width; j++) {
    const vals = body.map(r => r[j]);
    if (vals.every(v => v === null || (typeof v === "string" && !pyStrip(v)))) continue;
    if (h !== null && !head) {
      // Python raises IndexError here (a crash); the port answers with a PlotkitError
      throw new PlotkitError(`header row ${h + 1} is outside the sheet (it has ${rows.length} rows)`, "check read.header_row");
    }
    let name = head && head[j] !== null ? pyStrip(cellStr(head[j])) : "";
    if (unitRow && unitRow[j] !== null && pyStrip(cellStr(unitRow[j]))) {
      const u = pyStrip(pyStrip(cellStr(unitRow[j])), "()[]");
      if (u && !name.includes(u) && !["-", "–", "—"].includes(u)) name = name ? `${name} (${u})` : u;
    }
    name = name || colLetter(j);
    const stem = name;
    for (let k = 2; columns.includes(name); k++) name = `${stem} ${k}`;
    const t = typed(vals, decimal);
    columns.push(name);
    dtypes.push(t.dtype);
    data.push(t.values);
    Object.defineProperty(letters, name, { value: colLetter(j), enumerable: true, writable: true, configurable: true });   // any name, even __proto__
  }
  if (!columns.length) throw new PlotkitError("no data columns found");
  return { columns, dtypes, data, letters, headerRow: h !== null ? h + 1 : null, dataStartRow: ds + 1 };
}

/** _typed: a column's values as numbers (>= 90% numbers), dates (>= 90% dates) or text. */
export function typed(vals: Cell[], decimal: string): { dtype: Dtype; values: Value[] } {
  const nonempty = vals.filter(v => v !== null && !(typeof v === "string" && !pyStrip(v)));
  const n = Math.max(1, nonempty.length);
  if (nonempty.filter(v => toNum(v, decimal) !== null).length >= 0.9 * n) {
    return { dtype: "float", values: vals.map(v => (v !== null ? toNum(v, decimal) ?? NaN : NaN)) };
  }
  const dates = nonempty.filter(v => isDateCell(v) || (typeof v === "string" && DATE_RE.test(pyStrip(v)))).length;
  if (dates >= 0.9 * n) return { dtype: "datetime", values: toDatetime(vals) };
  return { dtype: "object", values: vals.map(v => (v !== null && pyStrip(cellStr(v)) ? pyStrip(cellStr(v)) : null)) };
}

// ------------------------------------------------------------------- pd.to_datetime(Series, errors="coerce")
const NAT_STRINGS = new Set(["NaT", "nat", "NAT", "nan", "NaN", "NAN"]);
const YMD = /^(\d{4})([-./])(\d{1,2})([-./])(\d{1,2})(?:([ T])(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?$/;

interface DateFormat { sep1: string; sep2: string; tsep: string | null; seconds: boolean }

function ymdMs(m: RegExpExecArray, minYear = 1): number {
  const y = +m[1], mo = +m[3], d = +m[5], hh = +(m[7] ?? 0), mi = +(m[8] ?? 0), ss = +(m[9] ?? 0);
  if (y < minYear || mo < 1 || mo > 12 || d < 1 || hh > 23 || mi > 59 || ss > 59) return NaN;
  const days = daysFromCivil(y, mo, d);
  if (isoFromMs(days * 86400000).slice(0, 10) !== `${m[1]}-${String(mo).padStart(2, "0")}-${String(d).padStart(2, "0")}`) return NaN;
  return days * 86400000 + (hh * 3600 + mi * 60 + ss) * 1000;
}

/** pandas' guess_datetime_format, for the date-time shapes plotkit takes for dates. */
function guessFormat(s: string): DateFormat | null {
  const m = YMD.exec(s);
  if (!m || Number.isNaN(ymdMs(m, 1000))) return null;
  return { sep1: m[2], sep2: m[4], tsep: m[6] ?? null, seconds: m[9] !== undefined };
}

function strictParse(s: string, f: DateFormat): number {
  const m = YMD.exec(s);
  if (!m || m[2] !== f.sep1 || m[4] !== f.sep2 || (m[6] ?? null) !== f.tsep || (m[9] !== undefined) !== f.seconds) return NaN;
  return ymdMs(m);
}

/** pd.to_datetime(values, errors="coerce") as epoch ms (NaN = NaT). When the first value is text with a date
 *  format, every text must have that format; otherwise each value is parsed on its own (pandas then falls back
 *  to dateutil for text that is not a plain date; here such text is NaT). */
export function toDatetime(vals: Cell[]): number[] {
  const skip = (v: Cell) => v === null || (typeof v === "string" && (v === "" || NAT_STRINGS.has(v) || v === "now" || v === "today"));
  const first = vals.find(v => !skip(v));
  const fmt = typeof first === "string" ? guessFormat(first) : null;
  return vals.map(v => {
    if (v === null) return NaN;
    if (isDateCell(v)) return msFromIso(v.date);
    if (typeof v === "string") {
      if (v === "" || NAT_STRINGS.has(v)) return NaN;
      if (fmt) return strictParse(v, fmt);
      const m = YMD.exec(v);
      return m ? ymdMs(m) : NaN;
    }
    if (typeof v === "number" && !fmt) return Math.trunc(v) / 1e6;                         // epoch nanoseconds
    return NaN;
  });
}

/** str(pd.Timestamp) of epoch ms: "YYYY-MM-DD HH:MM:SS". */
export function timestampStr(ms: number): string {
  return isoFromMs(ms).replace("T", " ");
}

// ------------------------------------------------------------------- load_frame
/** What load_frame reads of a chart spec. */
export interface FrameSpec {
  file: unknown[];
  sheets?: unknown;
  read?: ReadOptions | null;
  [key: string]: unknown;
}

/** load_frame: the table a chart spec asks for, as one Frame (several sheets/files stacked, with "sheet" and
 *  "file" columns). */
export async function loadFrame(spec: FrameSpec, files: InputFile[]): Promise<Frame> {
  const frames: Frame[] = [];
  const ro: ReadOptions = spec.read ?? {};
  const manyFiles = spec.file.length > 1;
  let letters: Record<string, string> | null = null;
  for (const fv of spec.file) {
    const f = pyStrOf(fv);
    const tables = await readTables(findFile(files, f), ro);
    const decimal = pyTruthy(ro.decimal) ? String(ro.decimal) : tables.decimal;
    const names = [...tables.sheets.keys()];
    const sel = spec.sheets;
    const chosen = sel === null || sel === undefined || sel === "" ? names.slice(0, 1) : selectSheets(names, sel, f);
    for (const n of chosen) {
      let d: Frame;
      try {
        d = frameFromRows(tables.sheets.get(n)!, decimal, ro.header_row, ro.data_start_row);
      } catch (e) {
        if (!(e instanceof PlotkitError)) throw e;
        throw new PlotkitError(`${pathName(f)} / sheet "${n}": ${e.message}`, e.hint);
      }
      letters ??= d.letters;
      if (chosen.length > 1) setColumn(d, "sheet", n);
      if (manyFiles) setColumn(d, "file", pathStem(f));
      frames.push({ columns: d.columns, dtypes: d.dtypes, data: d.data, letters: d.letters });
    }
  }
  if (!frames.length) throw new PlotkitError("no sheet to read", "check sheets");   // Python: IndexError
  const df = frames.length === 1 ? frames[0] : concat(frames);
  return { columns: df.columns, dtypes: df.dtypes, data: df.data, letters: letters ?? {} };
}

/** df[name] = value (a text column; replaces a column of that name in place). */
function setColumn(d: Frame, name: string, value: string): void {
  const n = d.data[0]?.length ?? 0;
  const i = d.columns.indexOf(name);
  const col = new Array<Value>(n).fill(value);
  if (i >= 0) {
    d.dtypes[i] = "object";
    d.data[i] = col;
  } else {
    d.columns.push(name);
    d.dtypes.push("object");
    d.data.push(col);
  }
}

/** pd.concat(frames, ignore_index=True, sort=False): columns in order of appearance; a column missing from a frame
 *  is NA there; columns of different types become object columns (dates there as str(Timestamp)). */
function concat(frames: Frame[]): Frame {
  const columns: string[] = [];
  for (const f of frames) for (const c of f.columns) if (!columns.includes(c)) columns.push(c);
  const dtypes: Dtype[] = [], data: Value[][] = [];
  for (const c of columns) {
    const kinds = new Set(frames.filter(f => f.columns.includes(c)).map(f => f.dtypes[f.columns.indexOf(c)]));
    const dtype: Dtype = kinds.size === 1 ? [...kinds][0] : "object";
    const out: Value[] = [];
    for (const f of frames) {
      const i = f.columns.indexOf(c);
      const n = f.data[0]?.length ?? 0;
      if (i < 0) {
        for (let k = 0; k < n; k++) out.push(dtype === "object" ? null : NaN);
        continue;
      }
      for (const v of f.data[i]) {
        if (dtype !== "object") out.push(v);
        else if (typeof v === "number" && Number.isNaN(v)) out.push(null);
        else out.push(f.dtypes[i] === "datetime" ? timestampStr(v as number) : v);
      }
    }
    dtypes.push(dtype);
    data.push(out);
  }
  return { columns, dtypes, data, letters: {} };
}

// ------------------------------------------------------------------- columns
/** find_col: a column of a loaded table by name, letter or part of its name. */
export function findCol(df: Frame, query: unknown, where: string): string {
  const q = pyStrip(pyStrOf(query));
  if (df.columns.includes(q)) return q;
  const letters = df.letters ?? {};
  if (/^[A-Za-z]{1,2}$/.test(q)) {
    const hit = Object.entries(letters).filter(([, l]) => l === q.toUpperCase()).map(([c]) => c);
    if (hit.length) return hit[0];
  }
  const qn = norm(q), qb = base(q);
  const scored: [number, string][] = [];
  for (const c of df.columns) {
    const n = norm(c), b = base(c);
    const s = n === qn ? 4 : qb && b === qb ? 3 : n.startsWith(qn) || (qb && b.startsWith(qb)) ? 2
      : n.includes(qn) || (qb && n.includes(qb)) ? 1 : 0;
    if (s) scored.push([s, c]);
  }
  if (!scored.length) {
    const m = getCloseMatches(q, df.columns.map(String), 2, 0.4);
    throw new PlotkitError(`${where}: no column matches "${pyStrOf(query)}"` + (m.length ? ` (closest: ${m.join(", ")})` : ""),
      "columns: " + df.columns.map(c => `${Object.hasOwn(letters, c) ? letters[c] : "?"} "${c}"`).join(", "));
  }
  const top = Math.max(...scored.map(([s]) => s));
  const best = scored.filter(([s]) => s === top).map(([, c]) => c);
  if (best.length > 1) throw new PlotkitError(`${where}: "${pyStrOf(query)}" matches several columns: ` + best.join(", "), "use more of the name, or the column letter");
  return best[0];
}
