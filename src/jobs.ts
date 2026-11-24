// Port of plotkit.core.build_jobs: read the sheets a normalized curve spec asks for and give, per sheet, the
// columns used per role and the finite data per role (shared by the curve engines).
import type { InputFile } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import {
  colList, findColumn, guessTgaColumns, loadSheets, pathName, pyTruthy, type Column, type SheetSpec, type Table,
} from "./reader.ts";

export type Role = "x" | "y1" | "y2";

/** The parts of a normalized curve spec (core.normalize_spec) that build_jobs reads. */
export interface CurveSpec extends SheetSpec {
  preset?: unknown;
  x: Record<string, unknown>;
  y1: Record<string, unknown>;
  y2: Record<string, unknown>;
  combine?: unknown;
  offset?: unknown;
  data_code?: unknown;
}

/** One sheet to draw. cols: the column per role (letter, index, name, values); data: the rows where every role
 *  has a finite number (y1/y2 flipped as the spec asks; y1 shifted by yoff when combined with an offset). */
export interface Job {
  file: string;
  sheet: string;
  cols: Partial<Record<Role, Column>>;
  how: string;
  data: Partial<Record<Role, number[]>>;
  rows: number;
  marks: Record<string, unknown>;
  yoff: number;
}

/** run_data_code: the spec's data_code on one sheet's arrays, in the host's sandbox. Returns the new data and the
 *  marks (normalized annotations), as plotkit.core.run_data_code does. */
export type DataCodeHook = (spec: CurveSpec, data: Partial<Record<Role, number[]>>, sheet: string) =>
  Promise<{ data: Partial<Record<Role, number[]>>; marks: Record<string, unknown> }>;

/** _flip: "flip" negates; "peaks_up" / "peaks_down" turn the curve so its largest excursion points that way. */
export function flip(v: number[], mode: unknown): number[] {
  if (mode === "flip") return v.map(x => -x);
  if (mode === "peaks_up" || mode === "peaks_down") {
    const f = v.filter(Number.isFinite);
    if (!f.length) return v;
    let max = -Infinity, min = Infinity;
    for (const x of f) { if (x > max) max = x; if (x < min) min = x; }
    const up = Math.abs(max) >= Math.abs(min);
    const w = up ? v : v.map(x => -x);
    return mode === "peaks_up" ? w : w.map(x => -x);
  }
  return v;
}

/** _resolve_columns: {role: column} (the spec's col, else the TGA guess) and how the guess was made. */
export function resolveColumns(spec: CurveSpec, table: Table, where: string): [Partial<Record<Role, Column>>, string] {
  const used: Partial<Record<Role, Column>> = {};
  const [guess, how] = spec.preset === "tga" ? guessTgaColumns(table) : [{} as Partial<Record<Role, Column>>, ""];
  for (const role of ["x", "y1", "y2"] as Role[]) {
    if (role === "y2" && !pyTruthy("show" in spec.y2 ? spec.y2.show : true)) continue;
    const q = spec[role].col;
    if (q !== null && q !== undefined && q !== "") used[role] = findColumn(table, q, `${where} ${role}.col`);
    else if (guess[role]) used[role] = guess[role];
    else if (role === "y2" && spec.preset !== "tga") continue;
    else {
      throw new PlotkitError(`${where}: could not tell which column is ${role}` + (spec.preset === "tga" ? " (TGA preset)" : ""),
        `set "${role}": {"col": "<letter>"}; columns: ` + colList(table.columns));
    }
  }
  return [used, how];
}

/** build_jobs: the jobs (one per sheet with at least 3 complete rows) and the warnings (sheets skipped). A spec
 *  with data_code needs dataCode (the sandbox); without it the spec is refused (where Python would run it). */
export async function buildJobs(spec: CurveSpec, files: InputFile[], dataCode?: DataCodeHook): Promise<[Job[], string[]]> {
  const sheets = await loadSheets(spec, files);
  const warnings: string[] = [];
  const jobs: Job[] = [];
  for (const [f, n, t] of sheets) {
    const where = `${pathName(f)} / "${n}"`;
    if (t instanceof PlotkitError) {
      warnings.push(`skipped ${where}: ${t.message}`);
      continue;
    }
    let cols: Partial<Record<Role, Column>>, how: string;
    try {
      [cols, how] = resolveColumns(spec, t, where);
    } catch (e) {
      if (e instanceof PlotkitError && sheets.length > 1 && (spec.sheets === "all" || spec.sheets === null || spec.sheets === undefined)) {
        warnings.push(`skipped ${where}: ${e.message}`);
        continue;
      }
      throw e;
    }
    let data: Partial<Record<Role, number[]>> = {};
    for (const role of Object.keys(cols) as Role[]) {
      const v = cols[role]!.values.slice();
      data[role] = role !== "x" ? flip(v, "flip" in spec[role] ? spec[role].flip : "none") : v;
    }
    const ok = data.x!.map(Number.isFinite);
    for (const role of Object.keys(data) as Role[]) data[role]!.forEach((v, i) => { if (!Number.isFinite(v)) ok[i] = false; });
    if (ok.filter(Boolean).length < 3) {
      warnings.push(`skipped ${where}: fewer than 3 complete rows`);
      continue;
    }
    for (const role of Object.keys(data) as Role[]) data[role] = data[role]!.filter((_, i) => ok[i]);
    let marks: Record<string, unknown> = {};
    if (pyTruthy(spec.data_code)) {
      if (!dataCode) throw new PlotkitError("data_code can not run here: no sandbox was given", "leave data_code out and use the spec keys");
      ({ data, marks } = await dataCode(spec, data, n));
    }
    jobs.push({ file: f, sheet: n, cols, how, data, rows: data.x!.length, marks, yoff: 0 });
  }
  if (!jobs.length) throw new PlotkitError("nothing to plot", warnings.join("; ") || "check the file");
  if (pyTruthy(spec.combine) && pyTruthy(spec.offset)) {
    jobs.forEach((j, k) => {
      j.yoff = k * Number(spec.offset);
      j.data.y1 = j.data.y1!.map(v => v + j.yoff);
    });
  }
  return [jobs, warnings];
}
