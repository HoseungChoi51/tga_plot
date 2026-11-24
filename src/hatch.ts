// The data hatch: model-written JavaScript ("data_code") run in the host's sandbox (RunCode; in KetchupE the QuickJS
// runner of electron/excel/sandbox.ts). plotkit builds the function body, the host runs it on JSON input and returns
// JSON. Non-finite numbers travel as null both ways (the host's encoder refuses them).
import { PlotkitError } from "./errors.ts";
import type { Frame, RunCode } from "./types.ts";

/** Array helpers for curve data_code (numpy's interp, gradient, ... on plain arrays). */
const CURVE_HELPERS = String.raw`
function interp(x0, xs, ys) {
  const n = xs.length;
  if (!n) return NaN;
  if (x0 <= xs[0]) return ys[0];
  if (x0 >= xs[n - 1]) return ys[n - 1];
  let lo = 0, hi = n - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] <= x0) lo = mid; else hi = mid; }
  const t = (x0 - xs[lo]) / (xs[hi] - xs[lo]);
  return ys[lo] + t * (ys[hi] - ys[lo]);
}
function gradient(ys, xs) {
  const n = ys.length, g = new Array(n);
  if (n < 2) return g.fill(NaN);
  if (!xs) xs = ys.map((_, i) => i);
  g[0] = (ys[1] - ys[0]) / (xs[1] - xs[0]);
  g[n - 1] = (ys[n - 1] - ys[n - 2]) / (xs[n - 1] - xs[n - 2]);
  for (let i = 1; i < n - 1; i++) {
    const h1 = xs[i] - xs[i - 1], h2 = xs[i + 1] - xs[i];
    g[i] = (h1 * h1 * ys[i + 1] - h2 * h2 * ys[i - 1] + (h2 * h2 - h1 * h1) * ys[i]) / (h1 * h2 * (h1 + h2));
  }
  return g;
}
function argmin(a) { let k = -1; for (let i = 0; i < a.length; i++) if (a[i] === a[i] && (k < 0 || a[i] < a[k])) k = i; return k; }
function argmax(a) { let k = -1; for (let i = 0; i < a.length; i++) if (a[i] === a[i] && (k < 0 || a[i] > a[k])) k = i; return k; }
function min(a) { const k = argmin(a); return k < 0 ? NaN : a[k]; }
function max(a) { const k = argmax(a); return k < 0 ? NaN : a[k]; }
function mean(a) { const v = a.filter(x => x === x); return v.length ? v.reduce((s, x) => s + x, 0) / v.length : NaN; }
function median(a) {
  const v = a.filter(x => x === x).sort((p, q) => p - q), n = v.length;
  return !n ? NaN : n % 2 ? v[(n - 1) >> 1] : (v[n / 2 - 1] + v[n / 2]) / 2;
}
`;

const FINITE = String.raw`
const __pk_num = (a) => a == null ? null : Array.from(a, v => v === null ? NaN : v);
const __pk_out = (v) => JSON.parse(JSON.stringify(v, (_k, w) => typeof w === "number" && !isFinite(w) ? null : w));
`;

/** The function body for a curve's data_code: input {x, y1, y2, sheet}; returns {x, y1, y2, marks}. */
export function curveProgram(code: string): string {
  return `${FINITE}${CURVE_HELPERS}
let x = __pk_num(input.x), y1 = __pk_num(input.y1), y2 = __pk_num(input.y2);
const sheet = input.sheet;
const marks = [];
${code}
;return __pk_out({x, y1, y2, marks});`;
}

/** Row objects whose keys may be given without their unit, as the Python sandbox allowed (df['수율'] also finds
 *  '수율 (g/g)'): reads and writes go to the one existing column the name matches, else to a new key. */
const ROW_PROXY = String.raw`
const __pk_norm = (s) => String(s).toLowerCase().replace(/[\s._\-:·,]+/g, "");
const __pk_base = (s) => __pk_norm(String(s).replace(/[\(\[\{].*?[\)\]\}]/g, ""));
function __pk_match(target, key) {
  if (typeof key !== "string" || key in target) return key;
  const hits = Object.keys(target).filter(c => __pk_base(c) === __pk_base(key) || __pk_norm(c) === __pk_norm(key));
  return hits.length === 1 ? hits[0] : key;
}
const __pk_row = (r) => new Proxy(r, {
  get: (t, k) => t[__pk_match(t, k)],
  set: (t, k, v) => { t[__pk_match(t, k)] = v; return true; },
  has: (t, k) => __pk_match(t, k) in t,
});
`;

/** The function body for a chart's data_code: input {columns, rows}; returns {rows}. */
export function chartProgram(code: string): string {
  return `${FINITE}${ROW_PROXY}
let rows = input.rows.map(__pk_row);
${code}
;if (!Array.isArray(rows)) throw new Error("data_code must leave an array of row objects in rows");
return __pk_out({rows: rows.map(r => Object.assign({}, r))});`;
}

async function run(runCode: RunCode | undefined, program: string, input: unknown, hint: string, signal?: AbortSignal) {
  if (!runCode) {
    throw new PlotkitError("data_code needs the app's sandbox, and none was given",
      "draw it with keys only (no data_code), or say in asks that it cannot be done");
  }
  try {
    return await runCode(program, input, signal);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new PlotkitError(`data_code failed: ${msg.split("\n").filter(Boolean).pop() ?? msg}`, hint);
  }
}

const numbers = (v: unknown): number[] | null =>
  Array.isArray(v) && v.every(x => x === null || typeof x === "number") ? v.map(x => (x === null ? NaN : (x as number))) : null;

/** A curve sheet's data_code. normalizeMark turns one mark into an annotation (plotkit's annotation rules). */
export async function runCurveDataCode(code: string, data: Record<string, number[]>, sheet: string, runCode: RunCode | undefined,
  normalizeMark: (name: string, mark: Record<string, unknown>) => Record<string, unknown>, signal?: AbortSignal):
  Promise<{ data: Record<string, number[]>; marks: Record<string, Record<string, unknown>> }> {
  const fin = (a: number[] | undefined) => (a ? a.map(v => (Number.isFinite(v) ? v : null)) : null);
  const out = await run(runCode, curveProgram(code), { x: fin(data.x), y1: fin(data.y1), y2: fin(data.y2), sheet },
    "names: x, y1, y2 (arrays of numbers), sheet, marks (an array), helpers interp, gradient, argmin, argmax, min, max, mean, median; reassign x/y1/y2 to change the curve",
    signal) as Record<string, unknown>;
  const fresh: Record<string, number[]> = {};
  for (const role of ["x", "y1", "y2"]) {
    if (!(role in data)) continue;
    const v = numbers(out?.[role]);
    if (!v) throw new PlotkitError(`data_code left ${role} as something that is not numbers`);
    fresh[role] = v;
  }
  const n = fresh.x.length;
  for (const [role, v] of Object.entries(fresh)) {
    if (v.length !== n) throw new PlotkitError(`data_code: ${role} has ${v.length} values but x has ${n}`, "keep x, y1 and y2 the same length");
  }
  const ok = fresh.x.map((v, i) => Number.isFinite(v) && Number.isFinite(fresh.y1[i]));
  for (const role of Object.keys(fresh)) fresh[role] = fresh[role].filter((_, i) => ok[i]);
  const raw = out?.marks ?? [];
  if (!Array.isArray(raw)) throw new PlotkitError("data_code: marks must be a list of dicts");
  const marks: Record<string, Record<string, unknown>> = {};
  raw.forEach((m, i) => {
    if (!m || typeof m !== "object" || Array.isArray(m)) {
      throw new PlotkitError("data_code: each mark must be a dict like {'type': 'vline', 'x': 605, 'text': 'Onset 605 °C'}");
    }
    const d = { ...normalizeMark(`mark${i + 1}`, m as Record<string, unknown>) };
    if (d.type === undefined) d.type = "text";
    const need = ({ vline: "x", hline: "y" } as Record<string, string>)[String(d.type)];
    if (need && (d[need] === undefined || d[need] === null)) throw new PlotkitError(`data_code: a ${d.type} mark needs "${need}"`);
    marks[`mark${i + 1}`] = d;
  });
  return { data: fresh, marks };
}

const pad = (n: number) => String(n).padStart(2, "0");
/** Epoch ms (a naive date-time read as UTC) -> "YYYY-MM-DD HH:MM:SS". */
export function dateText(ms: number): string | null {
  if (!Number.isFinite(ms)) return null;
  const d = new Date(ms);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}
const DATE_TEXT = /^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$/;

/** A chart's data_code on the loaded table: rows out, the new table back. Columns keep their order, new keys are
 *  appended; a column is numbers when all its values are numbers, dates when it was dates and still holds date text. */
export async function runChartDataCode(code: string, frame: Frame, runCode: RunCode | undefined, signal?: AbortSignal): Promise<Frame> {
  const n = frame.data[0]?.length ?? 0;
  const rows: Record<string, unknown>[] = [];
  for (let i = 0; i < n; i++) {
    const r: Record<string, unknown> = {};
    frame.columns.forEach((c, j) => {
      const v = frame.data[j][i];
      r[c] = frame.dtypes[j] === "datetime" ? dateText(v as number) : typeof v === "number" && !Number.isFinite(v) ? null : v;
    });
    rows.push(r);
  }
  const out = await run(runCode, chartProgram(code), { columns: frame.columns, rows },
    "names: rows (an array of objects, one per row, keyed by column name; dates as text); change them or assign a new array to rows",
    signal) as { rows?: unknown };
  if (!Array.isArray(out?.rows)) throw new PlotkitError("data_code must leave an array of row objects in rows");
  const outRows = out.rows as Record<string, unknown>[];
  const columns: string[] = [];
  for (const r of outRows) for (const k of Object.keys(r ?? {})) if (!columns.includes(k)) columns.push(k);
  const was = new Map(frame.columns.map((c, j) => [c, frame.dtypes[j]]));
  const dtypes: Frame["dtypes"] = [];
  const data: Frame["data"] = [];
  for (const c of columns) {
    const vals = outRows.map(r => (r && c in r ? r[c] : null));
    const present = vals.filter(v => v !== null && v !== undefined);
    if (was.get(c) === "datetime" && present.every(v => typeof v === "string" && DATE_TEXT.test(v))) {
      dtypes.push("datetime");
      data.push(vals.map(v => (typeof v === "string" ? Date.parse(v.replace(" ", "T") + (v.length === 10 ? "T00:00:00" : "") + "Z") : NaN)));
    } else if (present.length && present.every(v => typeof v === "number")) {
      dtypes.push("float");
      data.push(vals.map(v => (typeof v === "number" ? v : NaN)));
    } else if (present.length && present.every(v => typeof v === "boolean") && present.length === vals.length) {
      dtypes.push("bool");
      data.push(vals as boolean[]);
    } else {
      dtypes.push("object");
      data.push(vals.map(v => (v === undefined ? null : (v as string | number | boolean | null))));
    }
  }
  const letters: Record<string, string> = {};
  for (const [c, l] of Object.entries(frame.letters)) if (columns.includes(c)) letters[c] = l;
  return { columns, dtypes, data, letters };
}
