// plotkit.charts in TypeScript, from the loaded table to the ECharts option: filters (apply_filter), the figure
// model (build_model: group, aggregate, bin, colour), the layout both engines follow (layout), the ECharts option
// (echarts_option), the live result (live_result), the values reported back and the Korean summary.
// The Python module is the reference: the same spec and table give the same model, options and values.
import type { Frame } from "./types.ts";
import { PlotkitError } from "./errors.ts";
import { formatValue, pyFormat, pyRepr, pyRound, PyFormatError, type PyValue } from "./pyfmt.ts";
import { getCloseMatches } from "./difflib.ts";
import { isColorLike, colormap, colormapNames, type Colormap } from "./colors.ts";
import { tickValues } from "./ticks.ts";
import { CHART_AGGS, CHART_GRAYS, CHART_HIGHLIGHT_GRAY, CHART_PALETTE, CHART_PERIODS, KOREAN_COLORS, LINESTYLES, LINESTYLE_NAMES } from "./tables.ts";
import {
  type Kind, type Ser, type Table, type Val, allclose, amax, amin, arange, cmpStr, col, corrcoef, cut, dateStr, datetimeStrs,
  floatText, fromFrame, groupVar, histogram, histogramBinEdges, intStr, isMidnight, isNA, isoFormat, isoToMs, linspace, msToDays,
  nancorr, npAround, npMean, npMedian, npStd, npSum, parseTimestamp, periodStart, polyfit1, pyFloat, pyLen, pyMax, pyMin,
  rint, rollingMean, setCol, specNum, specRepr, specStr, stripQuotes, sub, take, truthy, tsStr,
} from "./chartdata.ts";

/* eslint-disable @typescript-eslint/no-explicit-any */
/** A normalized chart spec (plotkit.charts.normalize), internal "_" keys included. */
export type ChartSpec = Record<string, any>;
/** The engine-neutral figure model build_model makes and layout completes. */
export type ChartModel = Record<string, any>;
/** An ECharts option (with "__fmt__…" / "__histbar__" / "__errorbar__" markers; see revive.ts). */
export type EChartsOption = Record<string, any>;
/** Checks an "echarts" patch and returns a clean copy (plotkit.echarts.validate_patch); raises PlotkitError. */
export type ValidatePatch = (patch: unknown) => Record<string, any>;

export interface ChartResult {
  ok: true;
  kind: "chart";
  engine: "echarts";
  options: EChartsOption[];
  saved: string[];
  warnings: string[];
  not_done: string[];
  values: Record<string, any>;
  chart: string;
  rows_used: number;
  rows_total: number;
}

const PALETTE = CHART_PALETTE as readonly string[];
const GRAYS = CHART_GRAYS as readonly string[];
const HIGHLIGHT_GRAY = CHART_HIGHLIGHT_GRAY;
const PERIODS = CHART_PERIODS as Record<string, string>;
const PT = 96 / 72;
const SOFT: Record<string, string> = {
  red: "#c0392b", green: "#2e8b57", blue: "#1f4e9c", orange: "#e07b1f", purple: "#7b3fa0", yellow: "#d4ac0d",
  gold: "#d4ac0d", gray: "#8c8c8c", grey: "#8c8c8c", brown: "#8c564b", pink: "#d6609a",
};
const KIND_KO: Record<string, string> = {
  bar: "막대", hbar: "가로 막대", line: "선", scatter: "산점도", histogram: "히스토그램", heatmap: "히트맵", pie: "원",
};

/** Python's `a or b`. */
function or<T, U>(a: T, b: U): T | U {
  return truthy(a) ? a : b;
}

const fmt = (v: number, spec: string) => formatValue(v, spec);

/** str.format(v) of a user's template; a template Python can not apply is a PlotkitError here. */
function applyFormat(template: string, v: PyValue): string {
  try {
    return pyFormat(template, [v]);
  } catch (e) {
    if (e instanceof PyFormatError) throw new PlotkitError(`the format "${template}" failed: ${e.kind}: ${e.message}`, 'write a format like "{:.1f}"');
    throw e;
  }
}

// =================================================================== plotkit.core helpers
function color(c: unknown, where: string): string {
  const s = specStr(c).trim();
  let c2 = Object.hasOwn(KOREAN_COLORS, s) ? (KOREAN_COLORS as Record<string, string>)[s] : s;
  if (/^[0-9a-fA-F]{6}$/.test(c2)) c2 = "#" + c2;
  if (!isColorLike(c2)) {
    throw new PlotkitError(`${where}: ${specRepr(c)} is not a color`, 'use a name like "red", "navy", "black" or a hex code like "#c0392b"');
  }
  return c2;
}

function linestyleName(v: unknown, where: string): string {
  const ls = specStr(v).trim().toLowerCase();
  if (!Object.hasOwn(LINESTYLES, ls)) throw new PlotkitError(`${where} ${specRepr(v)} unknown`, "use solid, dashed, dotted or dashdot");
  return (LINESTYLE_NAMES as Record<string, string>)[(LINESTYLES as Record<string, string>)[ls]];
}

function unit(name: string | null | undefined): string | null {
  const m = /[(\[]\s*([^()\[\]]+?)\s*[)\]]\s*$/.exec(name || "");
  return m ? m[1] : null;
}

function normName(s: unknown): string {
  return specStr(s).toLowerCase().replace(/[\s._\-:·,]+/g, "");
}

function baseName(s: unknown): string {
  return normName(specStr(s).replace(/[([{].*?[)\]}]/g, ""));
}

function notDone(spec: ChartSpec): string[] {
  const asks = or(spec.asks, []);
  return (Array.isArray(asks) ? asks : []).filter((a: any) => a && typeof a === "object" && !Array.isArray(a) &&
    ["unsupported", "no", "none", "not_done"].includes(specStr(a.how ?? "").toLowerCase())).map((a: any) => specStr(a.ask ?? ""));
}

function toNum(v: unknown): number | null {
  if (v === null || v === undefined || typeof v === "boolean") return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v !== "string") return null;
  const s = v.trim().replace(/−/g, "-").replace(/ /g, "");
  if (!s || !/^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/.test(s)) return null;
  return parseFloat(s);
}

// =================================================================== columns
// A local port of plotkit.charts.find_col (ts/src/frame.ts holds the shared one): deduplicate later.
function findCol(t: Table, query: unknown, where: string): string {
  const q = specStr(query).trim();
  if (t.columns.includes(q)) return q;
  const letters = t.letters;
  if (/^[A-Za-z]{1,2}$/.test(q)) {
    const hit = Object.entries(letters).filter(([, l]) => l === q.toUpperCase()).map(([c]) => c);
    if (hit.length) return hit[0];
  }
  const qn = normName(q), qb = baseName(q);
  const scored: [number, string][] = [];
  for (const c of t.columns) {
    const n = normName(c), b = baseName(c);
    const s = n === qn ? 4 : (qb && b === qb) ? 3 : (n.startsWith(qn) || (qb && b.startsWith(qb))) ? 2
      : (n.includes(qn) || (qb && n.includes(qb))) ? 1 : 0;
    if (s) scored.push([s, c]);
  }
  if (!scored.length) {
    const m = getCloseMatches(q, t.columns.map(String), 2, 0.4);
    throw new PlotkitError(`${where}: no column matches "${specStr(query)}"` + (m.length ? ` (closest: ${m.join(", ")})` : ""),
      "columns: " + t.columns.map(c => `${letters[c] ?? "?"} "${c}"`).join(", "));
  }
  const top = amax(scored.map(([s]) => s));
  const best = scored.filter(([s]) => s === top).map(([, c]) => c);
  if (best.length > 1) {
    throw new PlotkitError(`${where}: "${specStr(query)}" matches several columns: ` + best.join(", "), "use more of the name, or the column letter");
  }
  return best[0];
}

/** Series.astype(str): null where pandas keeps the value missing. */
function astypeStr(s: Ser): (string | null)[] {
  if (s.kind === "M") return datetimeStrs(s.v as number[]);
  return s.v.map(v => {
    if (isNA(s.kind, v)) return null;
    if (typeof v === "string") return v;
    if (typeof v === "boolean") return v ? "True" : "False";
    if (s.kind === "i" || (s.kind === "O" && Number.isInteger(v))) return intStr(v as number);
    return pyRepr(v as number);
  });
}

/** _cat_label: the text of a category value (dates without a time of day as the date alone). */
function catLabel(kind: Kind, v: Val): string {
  if (kind === "M") {
    const ms = v as number;
    if (Number.isNaN(ms)) return "NaT";
    return isMidnight(ms) ? dateStr(ms) : tsStr(ms);
  }
  if (v === null) return "None";
  if (typeof v === "string") return v;
  if (typeof v === "boolean") return v ? "True" : "False";
  if (kind === "i" || Number.isInteger(v)) return intStr(v);
  return pyRepr(v);
}

function mapLabels(s: Ser): Ser {
  return { kind: "O", v: s.v.map(v => catLabel(s.kind, v)) };
}

/** _floats: the column as floats (text that holds numbers too); other text is a PlotkitError naming the column. */
function floats(s: Ser, col: string): number[] {
  if (s.kind === "M") throw new PlotkitError(`"${col}" holds dates, not numbers`, "pick a numeric column");
  return s.v.map(v => {
    if (v === null) return NaN;
    if (typeof v === "number") return v;
    if (typeof v === "boolean") return v ? 1 : 0;
    const x = floatText(v);
    if (x === null) throw new PlotkitError(`"${col}" holds text, not numbers`, "pick a numeric column, or use count or nunique");
    return x;
  });
}

const AGGS = CHART_AGGS as readonly string[];

/** _check_agg: aggregates other than count and nunique need numbers; on text (first / last aside: they may hold
 *  numbers) or dates they are a PlotkitError naming the aggregate and the column. */
function checkAgg(s: Ser, how: string, col: string): void {
  if (!AGGS.includes(how)) throw new PlotkitError(`unknown aggregate "${how}"`, "use one of: " + AGGS.join(", "));
  const k = s.kind;
  if (how === "count" || how === "nunique" || k === "f" || k === "i" || k === "b" || (k !== "M" && (how === "first" || how === "last"))) return;
  throw new PlotkitError(`cannot take the ${how} of "${col}": it holds ${k === "M" ? "dates" : "text"}`, "use count or nunique, or a numeric column");
}

/** _missing: missing category values: NaN, None, NaT, and blank text. */
function missing(s: Ser): boolean[] {
  return s.v.map(v => isNA(s.kind, v) || (s.kind === "O" && typeof v === "string" && v.trim() === ""));
}

/** _leave_out: rows whose category (x, by, the pie labels, the heatmap rows and columns) is missing are left out, the
 *  same for every chart: raw is the column, key what it groups by (a period or a bin; null outside the bins). Adds one
 *  note each for the missing and the out-of-bins rows and counts them out of rows_used. Returns the rows kept. */
function leaveOut(model: ChartModel, raw: Ser, key: Ser, col: string): number[] {
  const miss = missing(raw), keyMiss = missing(key);
  const out = keyMiss.map((m, i) => m && !miss[i]);
  for (const [n, what] of [[miss.filter(Boolean).length, `with no ${col}`], [out.filter(Boolean).length, `outside the bins of ${col}`]] as const) {
    if (n) model.notes.push(`${n} ${n === 1 ? "row" : "rows"} ${what} left out`);
  }
  const keep = miss.flatMap((m, i) => m || out[i] ? [] : [i]);
  if (!keep.length) {
    throw new PlotkitError(`no rows left after leaving out the rows with no ${col}` + (out.some(Boolean) ? " or outside its bins" : ""),
      "pick another column, or check the filters and bins");
  }
  model.rows_used -= raw.v.length - keep.length;
  return keep;
}

// =================================================================== filters
function parseValue(v: unknown, s: Ser): number | string {
  if (typeof v === "string") v = stripQuotes(v.trim());
  if (s.kind === "M") return parseTimestamp(specStr(v));
  if (s.kind === "f") {
    const x = typeof v === "number" || typeof v === "boolean" ? Number(v) : toNum(v);
    if (x === null) throw new PlotkitError(`"${specStr(v)}" is not a number, but that column holds numbers`);
    return x;
  }
  return specStr(v);
}

function splitList(rhs: string): string[] {
  rhs = rhs.trim();
  if ("[(".includes(rhs.slice(0, 1)) && "])".includes(rhs.slice(-1))) rhs = rhs.slice(1, -1);
  return rhs.split(/\s*,\s*/).filter(p => p.trim()).map(p => stripQuotes(p.trim()));
}

/** Element-wise comparison of a column with a value (pandas: missing compares False). */
function cmpMask(s: Ser, op: string, v: number | string): boolean[] {
  return s.v.map(x => {
    if (isNA(s.kind, x)) return false;
    let c: number;
    if (typeof x === "number" && typeof v === "number") c = x < v ? -1 : x > v ? 1 : 0;
    else if (typeof x === "string" && typeof v === "string") c = cmpStr(x, v);
    else if (op === "==") return false;
    else throw new PlotkitError(`'${op}' not supported between ${typeof x === "string" ? "text" : "numbers"} and ${typeof v === "string" ? "text" : "a number"}`,
      "compare a number column with a number, or a text column with == or in");
    return op === ">" ? c > 0 : op === ">=" ? c >= 0 : op === "<" ? c < 0 : op === "<=" ? c <= 0 : c === 0;
  });
}

const ONE_DAY_LESS_1US = 86400000 - 0.001;

/** One filter condition (string, dict or [col, op, value]) -> a row mask. */
function filterMask(t: Table, cond: unknown): boolean[] {
  if (cond && typeof cond === "object" && !Array.isArray(cond)) {
    const d = cond as Record<string, any>;
    if ("col" in d || "column" in d) {
      const c0 = "col" in d ? d.col : d.column;
      const op = "op" in d ? d.op : "==", val = "value" in d ? d.value : d.values;
      if ("min" in d || "max" in d) {
        let m = new Array<boolean>(t.nrows).fill(true);
        const c = findCol(t, c0, "filter");
        const s = col(t, c);
        if (d.min !== null && d.min !== undefined) { const r = cmpMask(s, ">=", parseValue(d.min, s)); m = m.map((x, i) => x && r[i]); }
        if (d.max !== null && d.max !== undefined) { const r = cmpMask(s, "<=", parseValue(d.max, s)); m = m.map((x, i) => x && r[i]); }
        return m;
      }
      return filterMask(t, [c0, op, val]);
    }
    let m = new Array<boolean>(t.nrows).fill(true);
    for (const [k, v] of Object.entries(d)) {
      const r = v && typeof v === "object" && !Array.isArray(v) ? filterMask(t, { col: k, ...v })
        : Array.isArray(v) ? filterMask(t, [k, "in", v]) : filterMask(t, [k, "==", v]);
      m = m.map((x, i) => x && r[i]);
    }
    return m;
  }
  let c0: unknown, op: unknown, val: unknown;
  if (Array.isArray(cond) && cond.length === 3) {
    [c0, op, val] = cond;
  } else {
    const text = specStr(cond).trim();
    let found = false;
    for (const op_ of [" not in ", " between ", " contains ", " in ", ">=", "<=", "!=", "==", ">", "<", "="]) {
      const i = text.toLowerCase().indexOf(op_);
      if (i > 0) {
        [c0, op, val] = [text.slice(0, i).trim(), op_.trim(), text.slice(i + op_.length).trim()];
        found = true;
        break;
      }
    }
    if (!found) {
      throw new PlotkitError(`cannot read the filter "${specStr(cond)}"`,
        'write "<column> <op> <value>", op: == != > >= < <= in, not in, between, contains');
    }
  }
  const c = findCol(t, c0, "filter");
  const s = col(t, c);
  const opl = specStr(op).toLowerCase();
  const o = ({ "=": "==", is: "==", eq: "==", ne: "!=", gt: ">", ge: ">=", lt: "<", le: "<=" } as Record<string, string>)[opl] ?? opl;
  if (o === "in" || o === "not in") {
    const vals = Array.isArray(val) ? val : splitList(specStr(val));
    const vv = vals.map(v => parseValue(v, s));
    let m: boolean[];
    if (s.kind !== "O") {
      const set = new Set(vv);
      m = s.v.map(x => set.has(x as any));
    } else {
      const set = new Set(vv.map(v => specStr(v)));
      m = astypeStr(s).map(x => x !== null && set.has(x));
    }
    return o === "not in" ? m.map(x => !x) : m;
  }
  if (o === "between") {
    let lo: unknown, hi: unknown;
    if (Array.isArray(val)) {
      [lo, hi] = [val[0], val[1]];
    } else {
      const parts = specStr(val).trim().replace(/^[[\]()]+|[[\]()]+$/g, "")
        .split(/\s+(?:and|to|~|-|부터|에서)\s+|\s*~\s*|\s*,\s*/).filter(p => p.trim());
      if (parts.length !== 2) throw new PlotkitError(`cannot read the range in "${specStr(cond)}"`, 'write "<column> between A and B"');
      [lo, hi] = parts;
    }
    const hiText = stripQuotes(specStr(hi).trim());
    const l = parseValue(lo, s);
    let h = parseValue(hi, s);
    if (s.kind === "M" && pyLen(hiText) <= 10) h = (h as number) + ONE_DAY_LESS_1US;   // a date alone: the whole day
    const a = cmpMask(s, ">=", l), b = cmpMask(s, "<=", h);
    return a.map((x, i) => x && b[i]);
  }
  if (o === "contains") {
    const needle = stripQuotes(specStr(val));
    return astypeStr(s).map(x => x !== null && x.includes(needle));
  }
  let v = parseValue(val, s);
  if (s.kind === "M" && (o === "<=" || o === ">") && pyLen(stripQuotes(specStr(val).trim())) <= 10) {
    v = (v as number) + ONE_DAY_LESS_1US;                            // "<= 2026-08-30" includes that day
  }
  if (o === "==" || o === "!=") {
    let m: boolean[];
    if (s.kind === "O") {
      const want = specStr(v);
      m = astypeStr(s).map(x => o === "==" ? x !== null && x === want : x === null || x !== want);
    } else {
      m = s.v.map(x => o === "==" ? x === v : !(x === v));
    }
    return m;
  }
  if (s.kind === "O") throw new PlotkitError(`"${o}" needs a number or date column, and "${c}" holds text`, "use == or in");
  if (![">", ">=", "<", "<="].includes(o)) throw new PlotkitError(`unknown filter operator "${specStr(op)}"`, "op: == != > >= < <= in, not in, between, contains");
  return cmpMask(s, o, v);
}

/** One filter condition on the table -> a boolean mask (plotkit.charts.apply_filter). */
export function applyFilter(frame: Frame, cond: unknown): boolean[] {
  return filterMask(fromFrame(frame), cond);
}

// =================================================================== figure model
/** _agg: one aggregate of a group's values; checkAgg(s, how, col) has accepted the column. */
function agg(s: Ser, how: string, col: string): number {
  if (how === "count") return s.v.length;
  const vals = s.v.filter(x => !isNA(s.kind, x));
  if (how === "nunique") return new Set(vals).size;
  if (!vals.length) return NaN;
  if (s.kind === "O" || s.kind === "M") {
    if (s.kind === "O" && (how === "first" || how === "last")) return floats({ kind: "O", v: [vals[how === "first" ? 0 : vals.length - 1]] }, col)[0];
    throw new PlotkitError(`cannot take the ${how} of "${col}": it holds ${s.kind === "M" ? "dates" : "text"}`, "use count or nunique, or a numeric column");
  }
  const x = vals.map(v => typeof v === "boolean" ? (v ? 1 : 0) : v as number);
  switch (how) {
    case "first": return x[0];
    case "last": return x[x.length - 1];
    case "mean": return npMean(x);
    case "sum": return npSum(x);
    case "median": return npMedian(x);
    case "min": return x.reduce((a, b) => (b < a ? b : a));
    case "max": return x.reduce((a, b) => (b > a ? b : a));
    case "std": return npStd(x);
  }
  throw new PlotkitError(`unknown aggregate "${how}"`, "use mean, sum, count, median, min, max, std, first, last or nunique");
}

type OVal = string | number | null;
type NKey = [number, number, string];

function naturalKey(v: OVal): NKey {
  if (typeof v === "number") return [0, v, ""];
  const s = v === null ? "None" : v;
  const m = /^(\P{Nd}*?)(\p{Nd}+(?:\.\p{Nd}+)?)([^\n]*)\n?$/u.exec(s);
  return m ? [1, parseFloat(asciiDigits(m[2])), m[1] + m[3]] : [2, 0.0, s];
}

function asciiDigits(s: string): string {
  let out = "";
  for (const ch of s) {
    if (ch === "." || (ch >= "0" && ch <= "9")) { out += ch; continue; }
    let cp = ch.codePointAt(0)!, k = 0;
    while (/\p{Nd}/u.test(String.fromCodePoint(cp - 1)) ) { cp--; k++; }   // Nd digits come in runs of ten, 0..9
    out += String(k % 10);
  }
  return out;
}

function cmpNKey(a: NKey, b: NKey): number {
  if (a[0] !== b[0]) return a[0] - b[0];
  if (a[1] !== b[1]) return a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0;
  return cmpStr(a[2], b[2]);
}

function labelOf(v: OVal): string {
  return typeof v === "number" ? catLabel("f", v) : v === null ? "None" : v;
}

/** np.nan_to_num(x, nan=-inf) */
function nanToNegInf(x: number): number {
  return Number.isNaN(x) ? -Infinity : x === Infinity ? Number.MAX_VALUE : x === -Infinity ? -Number.MAX_VALUE : x;
}

/** _order: a given list first, by value (desc/asc), or natural order (R2 before R10). */
function order<T extends OVal>(values: T[], how: unknown, byValue?: Map<T, number>): T[] {
  const vals = [...values];
  if (Array.isArray(how)) {
    const want = how.map(specStr);
    const lab = new Map<string, T>();
    for (const v of vals) lab.set(labelOf(v), v);
    const first = want.filter(w => lab.has(w)).map(w => lab.get(w) as T);
    return [...first, ...vals.filter(v => !first.includes(v))];
  }
  if (typeof how === "string" && ["desc", "asc", "내림차순", "오름차순", "descending", "ascending"].includes(how) && byValue) {
    const rev = ["desc", "내림차순", "descending"].includes(how);
    const key = (v: T) => nanToNegInf(byValue.has(v) ? byValue.get(v)! : NaN);
    const keyed = vals.map(v => [key(v), v] as const);
    keyed.sort((a, b) => rev ? (b[0] > a[0] ? 1 : b[0] < a[0] ? -1 : 0) : (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    return keyed.map(k => k[1]);
  }
  const keyed = vals.map(v => [naturalKey(v), v] as const);
  keyed.sort((a, b) => cmpNKey(a[0], b[0]));
  return keyed.map(k => k[1]);
}

function periodKey(s: Ser, period: unknown): Ser {
  const p = PERIODS[specStr(period).toLowerCase()];
  if (p === undefined) throw new PlotkitError(`unknown period "${specStr(period)}"`, "use day, week, month, quarter or year");
  if (s.kind !== "M") throw new PlotkitError("x.period needs a date column", "pick the date column as x");
  return { kind: "M", v: (s.v as number[]).map(ms => periodStart(ms, p)) };
}

/** A user's colour, with plain names (red, 초록, ...) drawn in a softer shade of the same hue. */
function named(c: unknown, where: string): string {
  const cc = color(c, where);
  return SOFT[cc.trim().toLowerCase()] ?? cc;
}

function colorsFor(spec: ChartSpec, names: string[]): Map<string, string> {
  const c = spec.colors;
  const out = new Map<string, string>();
  if (typeof c === "string" && ["mono", "흑백", "black and white", "bw", "grayscale", "gray", "grey"].includes(c.toLowerCase())) {
    names.forEach((n, i) => out.set(n, GRAYS[i % GRAYS.length]));
    return out;
  }
  if (Array.isArray(c)) {
    if (!c.length && names.length) throw new PlotkitError("colors: the list is empty", "give one colour per series");
    names.forEach((n, i) => out.set(n, named(c[i % c.length], "colors")));
    return out;
  }
  if (c && typeof c === "object") {
    const lower = new Map<string, unknown>();
    for (const [k, v] of Object.entries(c)) lower.set(k.trim().toLowerCase(), v);
    names.forEach((n, i) => {
      const v = Object.hasOwn(c, n) ? c[n] : lower.get(n.trim().toLowerCase());
      out.set(n, truthy(v) ? named(v, `colors.${n}`) : PALETTE[i % PALETTE.length]);
    });
    return out;
  }
  if (typeof c === "string" && c) {
    const cc = named(c, "colors");
    names.forEach(n => out.set(n, cc));
    return out;
  }
  names.forEach((n, i) => out.set(n, PALETTE[i % PALETTE.length]));
  return out;
}

function legendTitle(name: string): string {
  return name.replace(/\s*[([][^()[\]]*[)\]]\s*$/, "");
}

/** A key that tells values apart as pandas' hashing does (NaN, None, numbers, text). */
function vkey(v: Val): string {
  if (v === null) return "null";
  if (typeof v === "number") return Number.isNaN(v) ? "nan" : "n" + (v === 0 ? 0 : v);
  if (typeof v === "boolean") return "n" + (v ? 1 : 0);
  return "s" + v;
}

/** An index of values with one number each (a pandas Series of aggregates). */
class Indexed {
  readonly keys: Val[] = [];
  readonly vals: number[] = [];
  private readonly at = new Map<string, number>();
  push(k: Val, v: number): void {
    const kk = vkey(k);
    if (!this.at.has(kk)) this.at.set(kk, this.keys.length);
    this.keys.push(k);
    this.vals.push(v);
  }
  has(k: Val): boolean { return this.at.has(vkey(k)); }
  get(k: Val, dflt = NaN): number { const i = this.at.get(vkey(k)); return i === undefined ? dflt : this.vals[i]; }
}

/** groupby(keys, sort=False) over the given rows: groups in order of first appearance, missing keys dropped. */
function groupRows(keys: Val[], kind: Kind, rows: number[]): { key: Val; rows: number[] }[] {
  const at = new Map<string, number>();
  const out: { key: Val; rows: number[] }[] = [];
  for (const i of rows) {
    const k = keys[i];
    if (isNA(kind, k)) continue;
    const kk = vkey(k);
    let g = at.get(kk);
    if (g === undefined) { g = out.length; at.set(kk, g); out.push({ key: k, rows: [] }); }
    out[g].rows.push(i);
  }
  return out;
}

/** groupby(labels) (sorted keys) of text labels -> [label, row positions]. */
function groupSorted(labels: string[]): [string, number[]][] {
  const m = new Map<string, number[]>();
  labels.forEach((l, i) => { const g = m.get(l); if (g) g.push(i); else m.set(l, [i]); });
  return [...m.entries()].sort((a, b) => cmpStr(a[0], b[0]));
}

function plain(s: Ser): (string | number)[] {
  if (s.kind === "M") return (s.v as number[]).map(isoFormat);
  if (s.kind === "f" || s.kind === "i") return s.v.map(v => v as number);
  return s.v.map(v => catLabelStr(v));
}

function catLabelStr(v: Val): string {
  return v === null ? "None" : typeof v === "string" ? v : typeof v === "boolean" ? (v ? "True" : "False") : (Number.isInteger(v) ? intStr(v) : pyRepr(v));
}

/** _as_float: numbers, or ISO dates as days since 1970 (matplotlib's date numbers). */
function asDays(xs: (string | number)[]): number[] {
  if (xs.length && typeof xs[0] === "string") return xs.map(x => msToDays(isoToMs(String(x))));
  return xs.map(x => typeof x === "number" ? x : pyFloat(x));
}

/** Build the engine-neutral figure: what to draw, with every number already computed (plotkit.charts.build_model).
 *  frame is the loaded table (with any data_code already applied by the caller). */
export function buildModel(spec: ChartSpec, frame: Frame): ChartModel {
  const kind: string = spec.chart;
  const notes: string[] = [];
  let df = fromFrame(frame);
  const nRows = df.nrows;
  let mask = new Array<boolean>(df.nrows).fill(true);
  for (const cond of spec.filter ?? []) {
    const m = filterMask(df, cond);
    mask = mask.map((x, i) => x && m[i]);
  }
  df = take(df, mask.flatMap((x, i) => x ? [i] : []));
  if (!df.nrows) throw new PlotkitError("no rows left after the filters", `filters: ${specRepr(spec.filter)}; check the values with preview`);
  const xs = spec.x ?? {}, ys = spec.y ?? {};
  const model: ChartModel = {
    kind, series: [], notes, rows_total: nRows, rows_used: df.nrows,
    x: { label: xs.label ?? null, type: "category" }, y: { label: ys.label ?? null, type: "value" }, refs: [],
  };
  let by: string | null = truthy(spec.by) ? findCol(df, spec.by, "by") : null;
  if (by) {
    df = take(df, leaveOut(model, col(df, by), col(df, by), by));
    model.legend_title = legendTitle(by);
  }
  if (kind === "heatmap") return heatmapModel(spec, df, model);
  if (kind === "histogram") return histModel(spec, df, model, by);

  const xcol = xs.col !== null && xs.col !== undefined ? findCol(df, xs.col, "x") : null;
  const ycols = ys.col;
  const ylist: unknown[] = Array.isArray(ycols) ? ycols : ycols !== null && ycols !== undefined ? [ycols] : [];
  const ycolNames = ylist.map(c => findCol(df, c, "y"));
  const aggHow: string | null = truthy(ys.agg) ? ys.agg : null;

  if (kind === "pie") {
    const lab = xcol ?? by;
    if (lab === null) throw new PlotkitError('pie needs the slice labels: "x": "<category column>"');
    const how = aggHow ?? (ycolNames.length ? "sum" : "count");
    if (how !== "count") {
      if (!ycolNames.length) throw new PlotkitError(`pie: "${how}" needs a y column`, 'add "y": "<value column>"');
      checkAgg(col(df, ycolNames[0]), how, ycolNames[0]);
    }
    df = take(df, leaveOut(model, col(df, lab), col(df, lab), lab));
    const labels0 = mapLabels(col(df, lab)).v as string[];
    const groups = groupSorted(labels0);
    const yser = ycolNames.length ? col(df, ycolNames[0]) : null;
    let vals = groups.map(([k, rows]) => [k, how === "count" ? rows.length : agg(sub(yser!, rows), how, ycolNames[0])] as [string, number]);
    vals = vals.filter(([, v]) => v > 0);
    const byv = new Map(vals);
    const ord = order(vals.map(([k]) => k), or(spec.sort, "desc"), byv);
    let labels = ord.map(String), values = ord.map(v => byv.get(v)!);
    const top = spec.top;
    if (truthy(top) && labels.length > pyInt(top)) {
      const t = pyInt(top);
      const rest = values.slice(t).reduce((a, b) => a + b, 0);
      labels = [...labels.slice(0, t), "기타"];
      values = [...values.slice(0, t), rest];
    }
    const tot = values.reduce((a, b) => a + b, 0);
    model.pie = { labels, values, shares: values.map(v => v / tot), colors: [...colorsFor(spec, labels).values()],
                  show: "values" in spec ? spec.values : "percent" };
    model.agg = how;
    model.value_name = ycolNames.length ? ycolNames[0] : "count";
    return model;
  }

  if (xcol === null) throw new PlotkitError(`${kind} needs "x"`, "columns: " + df.columns.join(", "));
  let xser = col(df, xcol);
  if (truthy(xs.period)) {
    xser = periodKey(xser, xs.period);
    model.x.period = xs.period;
  } else if (truthy(xs.bins) && ["bar", "hbar", "line"].includes(kind)) {
    xser = binSeries(xser, xs.bins);
  }
  if (kind !== "scatter") {                          // a scatter leaves out its points without x or y itself
    const keep = leaveOut(model, col(df, xcol), xser, xcol);
    df = take(df, keep);
    xser = sub(xser, keep);
  }
  const isNumX = (xser.kind === "f" || xser.kind === "i") && (kind === "line" || kind === "scatter");
  const isTimeX = xser.kind === "M";
  model.x.type = isTimeX && (kind === "line" || kind === "scatter") ? "time" : isNumX ? "value" : "category";
  model.x.label = or(model.x.label, xcol);
  if ((kind === "bar" || kind === "hbar") && isTimeX) xser = mapLabels(xser);

  if (ycolNames.length > 1 && by) throw new PlotkitError('use either several y columns or "by", not both');
  let hlWant: string[] | null = null;
  if (kind === "scatter" && spec.highlight !== null && spec.highlight !== undefined) {
    const hl = spec.highlight;
    hlWant = (Array.isArray(hl) ? hl : [hl]).map(specStr);
    if (!by) {                                     // find the column the highlighted value lives in
      const cand = df.columns.filter((c, j) => df.kinds[j] === "O" && hlWant!.every(w => astypeStr(col(df, c)).some(x => x === w)));
      if (cand.length !== 1) throw new PlotkitError(`highlight ${specRepr(hl)}: cannot tell which column it is in`, 'add "by": "<column>"');
      const strs = astypeStr(col(df, cand[0]));
      df = setCol(df, "__hl", { kind: "O", v: strs.map(x => x !== null && hlWant!.includes(x) ? x : "기타") });
      model.legend_title = legendTitle(cand[0]);
      by = "__hl";
    }
  }
  if (kind === "scatter") return scatterModel(spec, df, model, xser, ycolNames, by, hlWant);

  // bar / hbar / line: aggregate y per x (and per series)
  let how: string | null = aggHow ?? (!ycolNames.length ? "count" : null);
  const X = xser.v, xkind = xser.kind;
  const S = by ? (mapLabels(col(df, by)).v as string[]) : null;
  const seen = new Set<string>();
  let dup = false;
  for (let i = 0; i < df.nrows; i++) {
    const k = vkey(X[i]) + "\u0000" + (S ? S[i] : "");
    if (seen.has(k)) { dup = true; break; }
    seen.add(k);
  }
  if (how === null) {
    how = dup || kind === "bar" || kind === "hbar" ? "mean" : "first";
    if (dup) notes.push(`several rows per ${xcol}${by ? " and " + by : ""}: the ${how === "mean" ? "mean" : how} is drawn`);
  }
  model.agg = how;
  for (const c of ycolNames) checkAgg(col(df, c), how, c);
  const allRows = [...Array(df.nrows).keys()];
  let seriesSpecs: [any, number[], string | null][] = [];
  if (by) {
    for (const [k, rows] of groupSorted(S!)) seriesSpecs.push([k, rows, ycolNames.length ? ycolNames[0] : null]);
    const names = order(seriesSpecs.map(t => t[0] as string), or(spec._by_order, "x"));
    seriesSpecs = seriesSpecs.map((t, i) => [names.indexOf(t[0]), i, t] as const).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map(t => t[2]);
  } else if (ycolNames.length > 1) {
    const shown = new Map<string, unknown>();
    for (const [k, v] of Object.entries(or(ys._names, {}) as Record<string, unknown>)) shown.set(findCol(df, k, "y"), v);
    seriesSpecs = ycolNames.map(c => [shown.has(c) ? shown.get(c) : c, allRows, c]);
  } else {
    seriesSpecs = [[ycolNames.length ? ycolNames[0] : "count", allRows, ycolNames.length ? ycolNames[0] : null]];
  }
  const per: [any, Indexed, [Indexed, Indexed] | Indexed | null][] = [];
  const countsN = new Map<any, Indexed>();
  for (const [name, rows, yc] of seriesSpecs) {
    let vals: Indexed;
    let groups: { key: Val; rows: number[] }[] | null = null;
    const ys_ = yc !== null ? col(df, yc) : null;
    if (!dup && ["first", "last", "mean", "sum", "max", "min", "median"].includes(how) && yc !== null) {
      vals = new Indexed();                         // one row per x: nothing to aggregate
      const cn = new Indexed();
      const yv = floats(sub(ys_!, rows), yc);
      rows.forEach((r, i) => { vals.push(X[r], yv[i]); cn.push(X[r], Number.isNaN(yv[i]) ? 0 : 1); });
      countsN.set(name, cn);
    } else {
      groups = groupRows(X, xkind, rows);
      vals = new Indexed();
      const cn = new Indexed();
      for (const g of groups) {
        vals.push(g.key, how === "count" || yc === null ? g.rows.length : agg(sub(ys_!, g.rows), how, yc));
        cn.push(g.key, g.rows.length);
      }
      countsN.set(name, cn);
    }
    let err: [Indexed, Indexed] | Indexed | null = null;
    if (truthy(spec.error) && yc !== null && ["bar", "hbar", "line"].includes(kind) && groups !== null) {
      const e = specStr(spec.error).toLowerCase();
      checkAgg(col(df, yc), ["minmax", "range", "min-max"].includes(e) ? "min" : "std", yc);
      const gv = groups.map(g => floats(sub(ys_!, g.rows), yc));
      if (["std", "sd", "표준편차"].includes(e) || ["sem", "se", "표준오차"].includes(e)) {
        const w = ["std", "sd", "표준편차"].includes(e) ? "std" : "sem";
        const ix = new Indexed();
        groups.forEach((g, i) => ix.push(g.key, groupVar(gv[i], w)));
        err = ix;
      } else if (["minmax", "range", "min-max"].includes(e)) {
        const lo = new Indexed(), hi = new Indexed();
        groups.forEach((g, i) => {
          const ok = gv[i].filter(v => !Number.isNaN(v));
          const mn = ok.length ? ok.reduce((a, b) => (b < a ? b : a)) : NaN, mx = ok.length ? ok.reduce((a, b) => (b > a ? b : a)) : NaN;
          lo.push(g.key, vals.vals[i] - mn);
          hi.push(g.key, mx - vals.vals[i]);
        });
        err = [lo, hi];
      } else {
        throw new PlotkitError(`unknown error "${specStr(spec.error)}"`, "use std, sem or minmax");
      }
    }
    per.push([name, vals, err]);
  }
  let allx: Val[] = [];
  const inAll = new Set<string>();
  for (const [, vals] of per) {
    const add: Val[] = [];
    for (const v of vals.keys) {
      const k = vkey(v);
      if (k !== "nan" && inAll.has(k)) continue;
      add.push(v);
    }
    for (const v of add) { allx.push(v); inAll.add(vkey(v)); }
  }
  if (model.x.type === "category") {
    const tot = new Map<OVal, number>();
    for (const [, vals] of per) {
      vals.keys.forEach((k, i) => {
        const v = vals.vals[i];
        const kk = k as OVal;
        if (typeof kk === "number" && Number.isNaN(kk)) return;
        tot.set(kk, (tot.has(kk) ? tot.get(kk)! : 0) + (Number.isNaN(v) ? 0 : v));
      });
    }
    const srt = or(or(xs.order, spec.sort), "x");
    allx = order(allx as OVal[], srt, tot);
    if (truthy(spec.top)) {
      allx = srt === "x" ? order(allx as OVal[], "desc", tot).slice(0, pyInt(spec.top)) : allx.slice(0, pyInt(spec.top));
    }
    model.x.categories = allx.map(v => catLabel(xkind, v));
  } else {
    allx = [...allx].sort((a, b) => (a as number) - (b as number));
  }
  const names = per.map(([n]) => specStr(n));
  const cmap = colorsFor(spec, names);
  for (const [name, vals, err] of per) {
    const empty = ["count", "sum", "nunique"].includes(how) ? 0.0 : NaN;
    const y = allx.map(v => vals.has(v) ? vals.get(v) : empty);
    const cn = countsN.get(name)!;
    const s: Record<string, any> = { name: specStr(name), color: cmap.get(specStr(name)), y, n: allx.map(v => cn.has(v) ? cn.get(v, 0) : 0) };
    if (model.x.type !== "category") s.x = xkind === "M" ? allx.map(v => isoFormat(v as number)) : allx.map(v => v as number);
    if (err !== null) {
      if (Array.isArray(err)) s.err = [allx.map(v => err[0].get(v)), allx.map(v => err[1].get(v))];
      else { const e = allx.map(v => err.get(v)); s.err = [e, e]; }
    }
    model.series.push(s);
  }
  const hl = spec.highlight;
  if (hl !== null && hl !== undefined && (kind === "bar" || kind === "hbar")) {
    const want = new Set((Array.isArray(hl) ? hl : [hl]).map(specStr));
    const base = truthy(spec.colors) ? model.series[0].color : PALETTE[1];
    for (const s of model.series) {
      s.bar_colors = model.x.categories.map((c: string) => want.has(c)
        ? (truthy(spec.colors) ? (colorsFor(spec, [c]).get(c) ?? base) : base) : HIGHLIGHT_GRAY);
    }
  }
  if (truthy(spec.smooth) && kind === "line") {
    const sm = spec.smooth;
    const w = sm && typeof sm === "object" && !Array.isArray(sm) ? sm.window : sm;
    const keep = sm && typeof sm === "object" && !Array.isArray(sm) && truthy(sm.raw);
    const wi = pyInt(w);
    const out: any[] = [];
    for (const s of model.series) {
      const smoothed = rollingMean(s.y, wi);
      if (keep) {
        out.push({ ...s, alpha: 0.35, width: 1.0, name: `${s.name}` });
        out.push({ ...s, y: smoothed, name: `${s.name} (${wi}점 이동평균)` });
      } else {
        out.push({ ...s, y: smoothed, name: model.series.length > 1 ? s.name : `${s.name} (${wi}점 이동평균)` });
      }
    }
    model.series = out;
    model.smooth = wi;
  }
  model.stack = truthy(spec.stack) && (kind === "bar" || kind === "hbar");
  model.legend_needed = model.series.length > 1;
  const units = new Set(ycolNames.map(unit).filter((u): u is string => !!u));
  let ylab = ycolNames.length === 1 ? ycolNames[0] : !ycolNames.length ? "count"
    : ycolNames.length === 2 ? ycolNames.join(" / ") : units.size === 1 ? `(${[...units][0]})` : "";
  if (!["first", "last"].includes(how) && ycolNames.length) ylab = how !== "mean" || dup ? `${ylab} (${how})` : ylab;
  else if (how === "count") ylab = "count";
  model.y.label = or(model.y.label, ylab);
  const vfmt = spec.values;
  if (truthy(vfmt)) {
    model.value_format = typeof vfmt === "string" && vfmt.includes("{") ? vfmt : null;
    model.value_labels = true;
    model.value_kind = ({ n: "n", count: "n", 개수: "n", 건수: "n", both: "both" } as Record<string, string>)[specStr(vfmt).toLowerCase()] ?? "value";
  }
  refs(spec, model, df, ycolNames.length ? ycolNames[0] : null);
  return model;
}

/** Python int() of a spec value. */
function pyInt(v: unknown): number {
  const x = typeof v === "string" ? (/^\s*[+-]?\d+\s*$/.test(v) ? parseInt(v, 10) : NaN) : typeof v === "boolean" ? Number(v) : Math.trunc(Number(v));
  if (!Number.isFinite(x)) throw new PlotkitError(`invalid literal for int(): ${specRepr(v)}`, "give a whole number");
  return x;
}

function scatterModel(spec: ChartSpec, df: Table, model: ChartModel, xser: Ser, ycolNames: string[], by: string | null,
                      hlWant: string[] | null): ChartModel {
  if (!ycolNames.length) throw new PlotkitError('scatter needs "y"');
  const groups: [string | null, number[]][] = !by ? [[null, [...Array(df.nrows).keys()]]] : groupSorted(mapLabels(col(df, by)).v as string[]);
  let names = groups.map(([k]) => k);
  if (by) names = order(names as string[], or(spec._by_order, "x"));
  let cmap = colorsFor(spec, by ? names as string[] : [ycolNames[0]]);
  if (hlWant) {
    const given = spec.colors && typeof spec.colors === "object" && !Array.isArray(spec.colors) ? spec.colors : {};
    cmap = new Map((names as string[]).map(n => [n, hlWant.includes(n) ? (Object.hasOwn(given, n) ? named(given[n], "colors") : PALETTE[1]) : HIGHLIGHT_GRAY]));
  }
  const gidx = new Map(groups);
  const yser = col(df, ycolNames[0]);
  for (const k of names) {
    const idx = gidx.get(k)!;
    const sx = sub(xser, idx), sy = sub(yser, idx);
    const ok = idx.map((_, i) => !isNA(sx.kind, sx.v[i]) && !isNA(sy.kind, sy.v[i]));
    const keep = idx.flatMap((_, i) => ok[i] ? [i] : []);
    model.series.push({ name: by ? specStr(k) : ycolNames[0], color: cmap.get(by ? k as string : ycolNames[0]),
                        x: plain(sub(sx, keep)), y: floats(sub(sy, keep), ycolNames[0]) });
  }
  model.y.label = or(model.y.label, ycolNames[0]);
  model.legend_needed = !!by;
  if (truthy(spec.trend)) {
    for (const s of model.series) {
      const xv = asDays(s.x);
      if (xv.length >= 3) {
        const [a, b] = polyfit1(xv, s.y);
        const r = corrcoef(xv, s.y);
        s.trend = { slope: a, intercept: b, r2: r * r, x: [amin(xv), amax(xv)] };
      }
    }
    model.trend_label = !!spec.trend && typeof spec.trend === "object" && !Array.isArray(spec.trend) && truthy(spec.trend.label);
  }
  refs(spec, model, df, ycolNames[0]);
  return model;
}

/** _bin_series: bin a numeric column into labels "a–b"; bins are closed on the left, [a, b), like a histogram
 *  (the last one also holds b), unless bins = {"edges": [...], "closed": "right"}. */
function binSeries(s: Ser, bins: any): Ser {
  if (!(s.kind === "f" || s.kind === "i")) throw new PlotkitError("bins need a numeric column");
  const v = s.v as number[];
  const ok = v.filter(x => !Number.isNaN(x));
  const edges = binEdges(ok, bins);
  const right = !!bins && typeof bins === "object" && !Array.isArray(bins) && specStr(bins.closed ?? "left").toLowerCase() === "right";
  if (edges.every(e => Number.isInteger(e)) && edges.slice(1).every((b, i) => b - edges[i] === 1) && allclose(ok, ok.map(rint))) {
    return { kind: "O", v: v.map(x => Number.isNaN(x) || x < edges[0] || x > edges[edges.length - 1] ? null : intStr(Math.trunc(x))) };   // week 3 stays "3"
  }
  let iv: ([number, number] | null)[];
  if (right) {
    iv = cut(v, edges, true, true);
  } else {
    const last = edges[edges.length - 1];
    iv = cut(v.map(x => x !== last ? x : last - 1e-9 * Math.max(1.0, Math.abs(last))), edges, false, false);
  }
  return { kind: "O", v: iv.map(p => p ? `${fmtNum(p[0])}–${fmtNum(p[1])}` : null) };
}

function fmtNum(v: number): string {
  return fmt(v, ".4g");
}

const BINS_HINT = 'e.g. "bins": 10, "bins": {"width": 0.5} or "bins": [0, 5, 10]';

/** _edge_list: bin edges given as a list: numbers, two or more, increasing. */
function edgeList(bins: unknown, where: string): number[] {
  const edges = Array.isArray(bins) ? bins.map(b => specNum(b, where)) : [];
  if (edges.length < 2 || edges.slice(1).some((b, i) => b <= edges[i])) {
    throw new PlotkitError(`"${where}" must be two or more increasing edges, not ${specRepr(bins)}`, BINS_HINT);
  }
  return edges;
}

/** _edges: bin edges from a count, {"width"}, {"edges"} or a list. */
function binEdges(v: number[], bins: any): number[] {
  v = v.filter(Number.isFinite);
  if (Array.isArray(bins)) return edgeList(bins, "bins");
  if (isDict(bins)) {
    const e = bins.edges;
    if (truthy(e) && !(Array.isArray(e) && e.length === 2 && (truthy(bins.width) || truthy(bins.step)))) return edgeList(e, "bins.edges");
    if (truthy(e)) bins = { ...bins, min: e[0], max: e[e.length - 1] };      // {"width": 1, "edges": [3, 28]}: a range cut every width
    const r = bins.range;
    if (Array.isArray(r) && r.length === 2) bins = { ...bins, min: r[0], max: r[1] };
    const w0 = or(bins.width, bins.step);
    if (!truthy(w0)) throw new PlotkitError('"bins" needs a "width" (or give a number of bins, or a list of edges)', BINS_HINT);
    if (!(specNum(w0, "bins.width") > 0)) throw new PlotkitError(`"bins.width" must be above 0, not ${specRepr(w0)}`, BINS_HINT);
    const w = specNum(w0, "bins.width");
    let lo: unknown = bins.min ?? null, hi: unknown = bins.max ?? null;      // the data's range only where the spec does not give it
    if (lo === null) lo = v.length ? amin(v) : null;
    if (hi === null) hi = v.length ? amax(v) : null;
    if (lo === null || hi === null) throw new PlotkitError("no numbers to bin", 'give "min" and "max" with the width, or check the filters');
    const lo2 = Math.floor(specNum(lo, "bins.min") / w) * w;
    const hi2 = specNum(hi, "bins.max");
    const n = Math.max(1, Math.trunc(Math.ceil((hi2 - lo2) / w - 1e-9)));
    const out: number[] = [];
    for (let i = 0; i <= n; i++) out.push(lo2 + i * w);
    if (lo2 + n * w < hi2) out.push(lo2 + (n + 1) * w);
    return out;
  }
  let n: number;
  if (bins === null || bins === undefined || bins === true || bins === "auto") {      // true, not 1: "bins": 1 is one bin
    n = Math.min(30, Math.max(5, Math.trunc(Math.ceil(Math.log2(Math.max(2, v.length)) + 1))));
  } else {
    const x = specNum(bins, "bins");
    if (!(x >= 1)) throw new PlotkitError(`"bins" must be a number of bins (1 or more), not ${specRepr(bins)}`, BINS_HINT);
    n = Math.trunc(x);
  }
  return histogramBinEdges(v, n);
}

function histModel(spec: ChartSpec, df: Table, model: ChartModel, by: string | null): ChartModel {
  const xs = spec.x ?? {};
  const xcol = xs.col !== null && xs.col !== undefined ? findCol(df, xs.col, "x") : null;
  if (xcol === null) throw new PlotkitError('histogram needs "x": the numeric column to count');
  const xser = col(df, xcol);
  if (!(xser.kind === "f" || xser.kind === "i")) throw new PlotkitError(`histogram: "${xcol}" is not numeric`, "for counts of a text column use chart bar with y count");
  const xv = xser.v as number[];
  const edges = binEdges(xv.filter(x => !Number.isNaN(x)), or(spec.bins, xs.bins));
  let groups: [string, number[]][] = !by ? [[xcol, [...Array(df.nrows).keys()]]] : groupSorted(mapLabels(col(df, by)).v as string[]);
  const names = by ? order(groups.map(([k]) => k), or(spec._by_order, "x")) : groups.map(([k]) => k);
  if (by) groups = groups.map((g, i) => [names.indexOf(g[0]), i, g] as const).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map(t => t[2]);
  const cmap = colorsFor(spec, names);
  for (const [k, rows] of groups) {
    const v = rows.map(i => xv[i]).filter(x => !Number.isNaN(x));
    const cnt = histogram(v, edges, truthy(spec.density));
    model.series.push({ name: k, color: cmap.get(k), counts: cnt, n: v.length, mean: v.length ? npMean(v) : null });
  }
  model.edges = [...edges];
  model.x = { label: or(xs.label, xcol), type: "value" };
  model.y.label = or(spec.y?.label, truthy(spec.density) ? "density" : "count");
  model.stack = truthy(spec.stack);
  model.legend_needed = !!by;
  refs(spec, model, df, xcol, "x");
  return model;
}

function heatmapModel(spec: ChartSpec, df: Table, model: ChartModel): ChartModel {
  const cmapName = spec.cmap;
  if (truthy(spec.corr)) {
    let cols: string[];
    const given = spec.corr;
    if (given === true || given === "all" || given === "*") cols = df.columns.filter((_, j) => df.kinds[j] === "f");    // true, not 1
    else if (Array.isArray(given)) cols = given.map((c: unknown) => findCol(df, c, "corr"));
    else throw new PlotkitError(`"corr" must be a list of columns or "all", not ${specRepr(given)}`, 'e.g. "corr": ["1존온도", "CNT수율"] or "corr": "all"');
    if (!cols.length) throw new PlotkitError('"corr" found no numeric columns', 'name the columns: "corr": ["A", "B"]');
    for (const c of cols) {
      const k = col(df, c).kind;
      if (!(k === "f" || k === "i" || k === "b")) throw new PlotkitError(`corr: "${c}" is not a numeric column`, 'give numeric columns, or "corr": "all"');
    }
    const m = nancorr(cols.map(c => floats(col(df, c), c)));
    model.heat = { rows: cols.map(String), cols: cols.map(String), z: m, cmap: or(cmapName, "RdBu_r"), vmin: -1.0, vmax: 1.0,
                   label: "r", values: "values" in spec ? spec.values : true };
    model.x = { label: or(spec.x?.label, ""), type: "category", categories: model.heat.cols };
    model.y = { label: or(spec.y?.label, ""), type: "category", categories: model.heat.rows };
    return model;
  }
  const xs = spec.x ?? {}, ys = spec.y ?? {}, zs = spec.z ?? {};
  if (xs.col === null || xs.col === undefined || ys.col === null || ys.col === undefined) {
    throw new PlotkitError('heatmap needs "x" and "y" (two columns), and "z" for the cell value (default: row count)',
      'or "corr": [columns] for a correlation matrix');
  }
  const xc = findCol(df, xs.col, "x"), yc = findCol(df, ys.col, "y");
  const keyOf = (c: string, a: any) => truthy(a.period) ? periodKey(col(df, c), a.period) : truthy(a.bins) ? binSeries(col(df, c), a.bins) : col(df, c);
  let xk = keyOf(xc, xs), yk = keyOf(yc, ys);
  for (const [c, which] of [[xc, "x"], [yc, "y"]] as const) {
    const keep = leaveOut(model, col(df, c), which === "x" ? xk : yk, c);
    df = take(df, keep);
    xk = sub(xk, keep);
    yk = sub(yk, keep);
  }
  const how: string = or(zs.agg, truthy(zs.col) ? "mean" : "count");
  const zc = truthy(zs.col) ? findCol(df, zs.col, "z") : null;
  if (zc) checkAgg(col(df, zc), how, zc);
  const X = mapLabels(xk).v as string[], Y = mapLabels(yk).v as string[];
  const cells = new Map<string, number[]>();
  for (let i = 0; i < df.nrows; i++) {
    const k = Y[i] + "\u0000" + X[i];
    const g = cells.get(k);
    if (g) g.push(i); else cells.set(k, [i]);
  }
  const zser = zc ? col(df, zc) : null;
  const vals = new Map<string, number>();
  for (const [k, rows] of cells) vals.set(k, how === "count" || zc === null ? rows.length : agg(sub(zser!, rows), how, zc));
  const uniq = (a: string[]) => [...new Set(a)];
  let xcats = order(uniq(X), or(xs.order, "x"));
  let ycats = order(uniq(Y), or(ys.order, "x"));
  if (truthy(xs.bins)) { const s = new Set(xcats); xcats = binOrder(xk).filter(c => s.has(c)); }
  if (truthy(ys.bins)) { const s = new Set(ycats); ycats = binOrder(yk).filter(c => s.has(c)); }
  const empty = ["count", "sum", "nunique"].includes(how) ? 0.0 : NaN;     // nothing counted is 0, an empty mean is blank
  const z = ycats.map(r => xcats.map(c => { const k = r + "\u0000" + c; return vals.has(k) ? vals.get(k)! : empty; }));
  model.heat = { rows: [...ycats], cols: [...xcats], z, cmap: or(cmapName, "viridis"), vmin: null, vmax: null,
                 label: or(zs.label, zc ? `${zc} (${how})` : "count"), values: "values" in spec ? spec.values : false };
  model.agg = how;
  model.x = { label: or(xs.label, xc), type: "category", categories: model.heat.cols };
  model.y = { label: or(ys.label, yc), type: "category", categories: model.heat.rows };
  return model;
}

/** Bin labels "a–b" in the order of their lower edge. */
function binOrder(s: Ser): string[] {
  const labs = [...new Set(s.v.filter(v => v !== null).map(v => catLabelStr(v)))];
  const key = (t: string) => pyFloat(t.slice(1).includes("–") ? t.split("–")[0] : t);
  return labs.map(t => [key(t), t] as const).sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0).map(t => t[1]);
}

function refs(spec: ChartSpec, model: ChartModel, df: Table, ycol: string | null, axis = "y"): void {
  let rs: any = or(spec.ref, []);
  if (rs && typeof rs === "object" && !Array.isArray(rs)) rs = [rs];
  if (!Array.isArray(rs)) rs = typeof rs === "string" ? [...rs] : [rs];
  for (const r of rs) {
    if (!r || typeof r !== "object" || Array.isArray(r)) throw new PlotkitError('each "ref" is a dict like {"y": 5.2, "text": "목표"} or {"y": "mean"}');
    let ax = "x" in r ? "x" : "y";
    const v = r[ax];
    let val: number | string, text: unknown;
    if (typeof v === "string" && ["mean", "평균", "median", "중앙값", "avg", "average"].includes(v.toLowerCase())) {
      if (ycol === null) throw new PlotkitError('"mean" needs a y column');
      const fn = ["median", "중앙값"].includes(v.toLowerCase()) ? "median" : "mean";
      const s = col(df, ycol);
      checkAgg(s, fn, ycol);
      const x = (s.v as number[]).filter(q => !Number.isNaN(q));
      val = fn === "median" ? (x.length ? npMedian(x) : NaN) : npMean(x);
      text = or(r.text, `${fn === "mean" ? "평균" : "중앙값"} ${fmt(val, ".3g")}`);
    } else {
      if (typeof v === "string" && (model[ax] ?? {}).type === "category") val = v;
      else val = !(typeof v === "string" && model.x?.type === "time") ? specNum(v, `ref.${ax}`) : v;
      text = r.text ?? null;
    }
    if (axis === "x" && ax === "y" && model.kind === "histogram") ax = "x";     // a histogram's mean line is vertical
    model.refs.push({ axis: ax, value: val, text, color: color(or(r.color, "#555555"), "ref.color"),
                      style: linestyleName("linestyle" in r ? r.linestyle : "style" in r ? r.style : "dashed", "ref.linestyle") });
  }
}

// =================================================================== layout (shared by both engines)
/** Axis limits on round tick values, and the tick step. */
function nice(lo: number, hi: number, nbins = 6): [number, number, number] {
  if (!(Number.isFinite(lo) && Number.isFinite(hi))) return [0.0, 1.0, 0.2];
  if (hi === lo) { lo = lo - 1; hi = hi + 1; }
  const t = tickValues(lo, hi, nbins);
  const step = t[1] - t[0];
  return [t[0] <= lo + 1e-12 ? t[0] : t[0] - step, t[t.length - 1] >= hi - 1e-12 ? t[t.length - 1] : t[t.length - 1] + step, step];
}

type Box = [number, number, number, number];

function boxOverlap(a: Box, b: Box): number {
  return Math.max(0.0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0.0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
}

/** Rough text width in px (CJK counts double). */
function tw(text: unknown, sizePx: number): number {
  let n = 0;
  for (const ch of specStr(text)) n += ch.codePointAt(0)! > 0x2e80 ? 2 : 1;
  return n * sizePx * 0.56;
}

const finite = (a: number[]) => a.filter(Number.isFinite);
const nanMax = (a: number[]) => { const f = a.filter(x => !Number.isNaN(x)); return f.length ? f.reduce((p, q) => (q > p ? q : p)) : NaN; };
const nanMin = (a: number[]) => { const f = a.filter(x => !Number.isNaN(x)); return f.length ? f.reduce((p, q) => (q < p ? q : p)) : NaN; };
const nanToNum = (x: number) => Number.isNaN(x) ? 0 : x === Infinity ? Number.MAX_VALUE : x === -Infinity ? -Number.MAX_VALUE : x;

/** Decisions both renderers follow, so they draw the same thing: value-axis limits and ticks, the legend corner for
 *  "best", label rotation, and heatmap text colours (plotkit.charts.layout). Completes the model in place. */
export function layout(spec: ChartSpec, model: ChartModel): ChartModel {
  const kind: string = model.kind;
  const fs: number = spec.font_size;
  const pw = spec.size[0] * 72 * 0.78, ph = spec.size[1] * 72 * 0.70;      // plot area in points (rough)
  const lims: Record<string, number[]> = {};
  if (kind === "bar" || kind === "hbar" || kind === "histogram") {
    let hi: number, lo: number;
    if (kind === "histogram") {
      let tops = new Array<number>(model.edges.length - 1).fill(0);
      for (const s of model.series) {
        const c: number[] = s.counts;
        tops = model.stack ? tops.map((t, i) => t + c[i]) : tops.map((t, i) => npMaximum(t, c[i]));
      }
      hi = tops.length ? nanMax(tops) : 1.0;
      lo = 0.0;
    } else {
      const vals: number[][] = model.series.map((s: any) => s.y);
      const ncat = vals.length ? vals[0].length : 0;
      const colv = (i: number) => vals.map(r => r[i]);
      const nansum = (a: number[]) => a.reduce((p, q) => p + (Number.isNaN(q) ? 0 : q), 0);
      let tops = [...Array(ncat).keys()].map(i => model.stack ? nansum(colv(i).map(v => Number.isNaN(v) ? v : Math.max(v, 0))) : nanMax(colv(i)));
      const bots = [...Array(ncat).keys()].map(i => model.stack ? nansum(colv(i).map(v => Number.isNaN(v) ? v : Math.min(v, 0))) : nanMin(colv(i)));
      for (const s of model.series) {
        if (truthy(s.err)) {
          const e1: number[] = s.err[1];
          tops = tops.map((t, i) => fmax(t, s.y[i] + nanToNum(e1[i])));
        }
      }
      if (!tops.length) throw new PlotkitError("zero-size array to reduction operation fmax which has no identity", "no categories left to draw");
      hi = nanMax(tops);
      lo = pyMin(0.0, nanMin(bots));
      for (const r of model.refs) if (r.axis === "y" && typeof r.value !== "string") hi = pyMax(hi, r.value);
    }
    const head = 1.04 + (model.value_labels ? 0.08 : 0);
    lims.v = [lo, hi > 0 ? hi * head : hi];
  } else if (kind === "line" || kind === "scatter") {
    const ysAll = finite(model.series.length ? model.series.flatMap((s: any) => s.y as number[]) : [0]);
    if (ysAll.length) {
      const mx = amax(ysAll), mn = amin(ysAll);
      const pad = 0.04 * or(or(mx - mn, Math.abs(mx)), 1);
      lims.v = [mn - pad, mx + pad];
    }
    if (kind === "scatter" && model.x.type === "value") {
      const xsAll = finite(model.series.flatMap((s: any) => (s.x as unknown[]).map(v => typeof v === "number" ? v : pyFloat(v))));
      if (xsAll.length) {
        const mx = amax(xsAll), mn = amin(xsAll);
        const pad = 0.04 * or(mx - mn, 1);
        lims.x = nice(mn - pad, mx + pad);
      }
    }
  }
  // the legend corner for "best": the corner that covers the least of what is drawn
  const where = spec.legend.where;
  const need = (truthy(model.legend_needed) || (kind === "scatter" && truthy(model.trend_label))) && kind !== "heatmap" && kind !== "pie";
  if (need && where === "best" && "v" in lims) {
    const names: string[] = model.series.map((s: any) => s.name);
    if (kind === "scatter" && truthy(model.trend_label)) names.push(...names.map(n => `${n} fit: y = 0.000x + 0.000, R² = 0.00`));
    const lfs = or(spec.legend.size, fs * 0.833);
    const bw = (amax(names.map(n => tw(n, lfs) / PT)) + 30) / pw;
    const bh = (names.length * lfs * 1.5 + 8) / ph;
    let best = "";
    for (let it = 0; it < 4; it++) {
      const [lo, hi] = lims.v;
      const boxes: Box[] = [];
      let pts: [number, number][] = [];
      const fy = (v: number) => (v - lo) / or(hi - lo, 1);
      if (kind === "bar" || kind === "hbar") {
        const n = model.x.categories.length, k = model.series.length;
        let bottom = new Array<number>(n).fill(0);
        model.series.forEach((s: any, si: number) => {
          (s.y as number[]).forEach((v, i) => {
            if (!Number.isFinite(v)) return;
            const w = 0.8 / n / (model.stack ? 1 : k);
            const x0 = (i + 0.1) / n + (model.stack ? 0 : si * w);
            const b0 = model.stack ? bottom[i] : 0;
            const top = fy(b0 + v) + (model.value_labels ? 0.06 : 0);
            const box: Box = [x0, fy(pyMin(b0, 0)), x0 + w, top];
            boxes.push(kind === "bar" ? box : [box[1], 1 - box[2], box[3], 1 - box[0]]);
          });
          if (model.stack) bottom = bottom.map((b, i) => b + nanToNum(s.y[i]));
        });
      } else if (kind === "histogram") {
        const e: number[] = model.edges;
        const span = or(e[e.length - 1] - e[0], 1);
        let bottom = new Array<number>(e.length - 1).fill(0);
        for (const s of model.series) {
          (s.counts as number[]).forEach((c, i) => {
            const b0 = model.stack ? bottom[i] : 0;
            boxes.push([(e[i] - e[0]) / span, 0, (e[i + 1] - e[0]) / span, fy(b0 + c)]);
          });
          if (model.stack) bottom = bottom.map((b, i) => b + s.counts[i]);
        }
      } else {
        for (const s of model.series) {
          let xv = s.x !== null && s.x !== undefined ? asDays(s.x) : (s.y as number[]).map((_, i) => i);
          let yv = [...s.y as number[]];
          const ok = xv.map((x, i) => Number.isFinite(x) && Number.isFinite(yv[i]));
          xv = xv.filter((_, i) => ok[i]);
          yv = yv.filter((_, i) => ok[i]);
          if (!xv.length) continue;
          if (kind === "line" && xv.length < 200) {           // points along the segments too
            const t = linspace(0, 1, 8).slice(0, -1);
            const interp = (a: number[]) => a.length > 1 ? [...a.slice(0, -1).flatMap((x, i) => t.map(tt => x + (a[i + 1] - x) * tt)), a[a.length - 1]] : a;
            xv = interp(xv);
            yv = interp(yv);
          }
          const [x0, x1] = "x" in lims ? [lims.x[0], lims.x[1]] : [amin(xv), amax(xv)];
          xv.forEach((x, i) => pts.push([(x - x0) / or(x1 - x0, 1), fy(yv[i])]));
        }
      }
      const m = 0.02;
      const corners: [string, Box][] = [
        ["upper right", [1 - bw - m, 1 - bh - m, 1 - m, 1 - m]], ["upper left", [m, 1 - bh - m, bw + m, 1 - m]],
        ["lower right", [1 - bw - m, m, 1 - m, bh + m]], ["lower left", [m, m, bw + m, bh + m]]];
      const cost = corners.map(([, c]) => boxes.length ? boxes.reduce((acc, b) => acc + boxOverlap(c, b), 0)
        : pts.filter(([px, py]) => px >= c[0] && px <= c[2] && py >= c[1] && py <= c[3]).length);
      let bi = 0;
      for (let i = 1; i < cost.length; i++) if (cost[i] < cost[bi]) bi = i;
      best = corners[bi][0];
      if (cost[bi] <= 1e-9 || !["bar", "histogram", "line", "scatter"].includes(kind) || ((kind === "line" || kind === "scatter") && it >= 1)) break;
      lims.v[1] = hi + (hi - lo) * 0.18;                // make room above and try again
    }
    model.legend_where = best;
  } else {
    model.legend_where = where;
  }
  if ("v" in lims) {
    let [lo] = lims.v;
    const hi = lims.v[1];
    if ((kind === "bar" || kind === "hbar" || kind === "histogram") && lo >= 0) lo = 0.0;
    lims.v = nice(lo, hi);
  }
  const scale = fs / 11;
  const nPts = kind === "scatter" ? model.series.reduce((a: number, s: any) => a + s.y.length, 0) : 0;
  const ps = spec.point_size, al = spec.alpha;          // numbers once normalized; checked, never taken raw
  model.point_size = ps !== null && ps !== undefined ? specNum(ps, "point_size") : (nPts > 300 ? 9 : 22) * (scale * scale);
  model.point_alpha = al !== null && al !== undefined ? specNum(al, "alpha") : nPts > 300 ? 0.55 : 0.9;     // 0 is a value
  if (kind === "line") {
    const dense = Math.max(0, ...model.series.map((s: any) => s.y.length)) > 500;
    for (const s of model.series) if (!("width" in s)) s.width = dense ? 1.0 : 1.8;
    if (model.x.type === "value" || model.x.type === "time") {           // a trend runs edge to edge
      const xsAll: (string | number)[] = model.series.flatMap((s: any) => or(s.x, []) as (string | number)[]);
      if (xsAll.length) {
        const xv = model.x.type === "time" ? asDays(xsAll) : xsAll.map(Number);
        lims.x_tight = [nanMin(xv), nanMax(xv)];
      }
    }
  }
  model.lims = lims;
  model.ticks = {};
  for (const k of ["v", "x"]) {
    if (k in lims) {                                  // limits on round values: ticks every step between them
      const [lo, hi, st] = lims[k];
      model.ticks[k] = arange(lo, hi + st / 2, st).map(v => npAround(v, 10));
    } else if (k === "x" && "x_tight" in lims && model.x.type === "value") {
      const [lo, hi] = lims.x_tight;
      model.ticks.x = tickValues(lo, hi, 6).filter(v => lo - 1e-9 <= v && v <= hi + 1e-9);
    }
  }
  if (kind === "histogram") {
    const e: number[] = model.edges;
    model.ticks.x = tickValues(e[0], e[e.length - 1], 6).filter(v => e[0] - 1e-9 <= v && v <= e[e.length - 1] + 1e-9);
  }
  // category labels: rotate when they do not fit side by side
  const cats: string[] = or(model.x.categories, []);
  let rot: any = spec.x.rotate ?? null;
  if (rot === null && cats.length && ["bar", "line", "heatmap"].includes(kind)) {
    const tick = fs * 0.9;
    const needW = cats.reduce((a, c) => a + (tw(c, tick) / PT + tick * 0.8), 0);
    const room = pw * (kind === "heatmap" ? 0.72 : 0.98);             // a heatmap gives width to its colour bar
    rot = needW > room ? (needW > 2.2 * room ? 90 : 45) : 0;
  }
  model.rotate_x = truthy(rot) ? specNum(rot, "x.rotate") : 0.0;
  if (kind === "heatmap") {
    const h = model.heat;
    const z: number[][] = h.z;
    const fin = z.flat().filter(Number.isFinite);
    const vmin = h.vmin !== null ? h.vmin : fin.length ? amin(fin) : 0;
    const vmax = h.vmax !== null ? h.vmax : fin.length ? amax(fin) : 1;
    const cm = colormap(h.cmap);
    if (!cm) {
      throw new PlotkitError(`unknown cmap "${specStr(h.cmap)}"`, "use one of: " + colormapNames().filter(n => !n.endsWith("_r")).join(", ") + ' (add "_r" to reverse)');
    }
    const tcol = z.map(row => row.map(v => !Number.isFinite(v) ? null : cm.dark((v - vmin) / or(vmax - vmin, 1)) ? "#ffffff" : "#000000"));
    h.text_colors = tcol;
    h.vmin_used = vmin;
    h.vmax_used = vmax;
    h.fill = z.map((zr, i) => zr.map((v, j) => tcol[i][j] === null ? null : cm.hex((v - vmin) / or(vmax - vmin, 1))));
  }
  return model;
}

/** np.maximum (NaN propagates) and np.fmax (NaN ignored). */
function npMaximum(a: number, b: number): number {
  return Number.isNaN(a) || Number.isNaN(b) ? NaN : Math.max(a, b);
}

function fmax(a: number, b: number): number {
  return Number.isNaN(a) ? b : Number.isNaN(b) ? a : Math.max(a, b);
}

// =================================================================== ECharts
function barTexts(model: ChartModel, s: any): string[] {
  const f: string = or(model.value_format, autoFmt(s.y));
  const vk = model.value_kind ?? "value";
  const n: (number | null)[] = or(s.n, null) ?? s.y.map(() => null);
  return (s.y as number[]).map((v, i) => {
    if (!Number.isFinite(v)) return "";
    const ni = n[i] === null ? "None" : String(n[i]);
    if (vk === "n") return `n=${ni}`;
    if (vk === "both") return `${applyFormat(f, v)} (n=${ni})`;
    return applyFormat(f, v);
  });
}

function autoFmt(v0: number[]): string {
  const v = finite(v0);
  if (!v.length) return "{:g}";
  const m = amax(v.map(Math.abs));
  if (allclose(v, v.map(rint))) return "{:.0f}";
  return m >= 100 ? "{:.0f}" : m >= 10 ? "{:.1f}" : m >= 1 ? "{:.2f}" : "{:.3f}";
}

function fontFamily(spec: ChartSpec, texts: unknown[]): string {
  if (truthy(spec.font)) return `${specStr(spec.font)}, sans-serif`;
  if (texts.some(t => /[가-힣ㄱ-ㆎ]/.test(truthy(t) ? specStr(t) : ""))) {
    return "Malgun Gothic, Apple SD Gothic Neo, AppleGothic, NanumGothic, Noto Sans CJK KR, Noto Sans KR, WenQuanYi Zen Hei, sans-serif";
  }
  return "DejaVu Sans, Arial, Helvetica, sans-serif";
}

/** ECharts lineStyle.type for solid / dashed / dotted / dashdot (dashdot has no keyword: a dash pattern). */
function echartsDash(style: string, width: number): string | number[] {
  return style === "dashdot" ? [6.4, 1.6, 1, 1.6].map(v => pyRound(v * pyMax(width, 1), 2)) : style;
}

/** decimals of f"{t:.10g}" */
function decimals(t: number): number {
  const s = fmt(t, ".10g");
  return s.includes(".") ? s.split(".")[1].length : 0;
}

/** The figure model as an ECharts option (static export, or live with tooltips and zoom), and the canvas size in px
 *  (plotkit.charts.echarts_option). */
export function echartsOption(spec: ChartSpec, model: ChartModel, live = false): [EChartsOption, [number, number]] {
  const kind: string = model.kind;
  const W = spec.size[0] * 96, H = spec.size[1] * 96;
  const fs = spec.font_size * PT;
  const tc = spec.text_color;
  const texts: unknown[] = [or(spec.title.text, ""), or(model.x.label, ""), or(model.y.label, ""),
    ...model.series.map((s: any) => s.name), ...(model.x.categories ?? []), ...(or(model.pie?.labels, []) as string[]),
    ...(or(model.heat?.rows, []) as string[])];
  const fam = fontFamily(spec, texts);
  const ts = { fontFamily: fam, color: tc, fontSize: fs };
  const title = spec.title.text;
  const tsize = or(spec.title.size, spec.font_size * 1.2);
  const opt: EChartsOption = {
    animation: false, backgroundColor: "#ffffff", textStyle: ts, useUTC: true,
    title: { show: truthy(title), text: or(title, ""), left: "center", top: 6,
             textStyle: { fontFamily: fam, color: or(spec.title.color, tc), fontSize: tsize * PT, fontWeight: "normal" } },
    series: [],
  };
  const lg = spec.legend;
  let showLeg = truthy(lg.show) && (truthy(model.legend_needed) || (kind === "scatter" && truthy(model.trend_label))) && kind !== "heatmap";
  if (kind === "pie" && truthy(lg.show) && String(lg.where).startsWith("outside")) showLeg = true;
  const top = 12 + (truthy(title) ? tsize * PT * 1.6 : 0);
  const grid: Record<string, number> = { left: 0, right: 0, top: top + 8, bottom: 0 };
  if (showLeg) {
    let names: unknown[] = kind !== "pie" ? model.series.map((s: any) => s.name) : model.pie.labels;
    const lfs = or(lg.size, spec.font_size * 0.833) * PT;
    const sc = spec.font_size / 11;
    const leg: Record<string, any> = { show: true, data: [...names], textStyle: { ...ts, fontSize: lfs }, itemWidth: 18 * sc,
                                       itemHeight: 10 * sc, orient: "vertical" };
    if (kind !== "pie" && (truthy(model.legend_title) || truthy(lg.title))) {      // a pie's legend lists its slices only
      const lt = or(lg.title, model.legend_title);
      leg.data = [{ name: lt, icon: "none", textStyle: { ...ts, fontSize: lfs, fontWeight: "bold" } }, ...leg.data];
      opt._legend_dummy = lt;                    // a name-only series, added after the data series
      names = [lt, ...names];
    }
    const lw = amax(names.map(n => tw(n, lfs))) + 30;
    const w = or(model.legend_where, lg.where);
    if (w === "outside right") {
      Object.assign(leg, { right: 8, top: "middle" });
      grid.right += lw + 8;
    } else if (w === "outside bottom") {
      Object.assign(leg, { orient: "horizontal", left: "center", bottom: 4 });
      grid.bottom += lfs * 2.2;
    }
    opt.legend = leg;
    opt._legend_where = w;
  }
  if (live) {
    opt.tooltip = { trigger: ["pie", "heatmap", "scatter"].includes(kind) ? "item" : "axis", confine: true };
    if (kind === "line" || kind === "scatter") {
      opt.dataZoom = kind === "scatter" ? [{ type: "inside" }, { type: "inside", orient: "vertical" }] : [{ type: "inside" }];
    }
  }
  if (kind === "pie") {
    const p = model.pie;
    const show = p.show;
    if (show !== null && typeof show === "object") throw new PlotkitError(`unhashable type: '${Array.isArray(show) ? "list" : "dict"}'`, '"values" for a pie: "percent", "value", "both" or false');
    const modes: Record<string, string> = { value: "value", 값: "value", both: "both", 둘다: "both" };
    const mode = typeof show === "string" && Object.hasOwn(modes, show) ? modes[show]
      : show === false || show === 0 || show === "none" ? "none" : "percent";
    const ptext = (n: string, v: number, sh: number) => mode === "none" ? n : mode === "value" ? `${n}\n${fmt(v, ".4g")}`
      : mode === "both" ? `${n}\n${fmt(v, ".4g")} (${fmt(sh * 100, ".1f")}%)` : `${n}\n${fmt(sh * 100, ".1f")}%`;
    const r = pyMin(W - grid.right, H - top) * 0.30;
    opt.series.push({
      type: "pie", radius: [0, r], center: [W / 2 - grid.right / 2, top + (H - top) / 2], startAngle: 90, clockwise: true,
      data: (p.labels as string[]).map((n, i) => ({ name: n, value: p.values[i], itemStyle: { color: p.colors[i] },
                                                    label: { formatter: ptext(n, p.values[i], p.shares[i]) } }))
        .slice(0, Math.min(p.labels.length, p.values.length, p.colors.length, p.shares.length)),
      label: { show: true, color: tc, fontFamily: fam, fontSize: fs * 0.9, overflow: "none" },
      labelLine: { length: 8, length2: 6 },
      itemStyle: { borderColor: "#ffffff", borderWidth: 1 },
    });
    placeLegend(opt, grid);
    return [opt, [W, H]];
  }
  // cartesian
  const xl: string = or(model.x.label, ""), yl: string = or(model.y.label, "");
  const catAxis = { type: "category", data: model.x.categories ?? [] };
  const valAxis = { type: "value", scale: false };
  let xa: Record<string, any>, ya: Record<string, any>;
  if (kind === "heatmap") {
    const h = model.heat;
    xa = { type: "category", data: h.cols, name: xl, splitArea: { show: false } };
    ya = { type: "category", data: h.rows, name: yl };
    const z: number[][] = h.z;
    const fin = z.flat().filter(Number.isFinite);
    const vmin: number = h.vmin_used, vmax: number = h.vmax_used;
    const mc = colormap(h.cmap) as Colormap;
    const cm = linspace(0, 1, 11).map(t => mc.hex(t));
    const f: string = typeof h.values === "string" && h.values.includes("{") ? h.values : autoFmt(fin);
    const ncol = z.length ? z[0].length : 0;
    const data: any[] = [];
    z.forEach((row, i) => {
      for (let j = 0; j < ncol; j++) {
        const v = row[j];
        data.push({ value: [j, i, !Number.isFinite(v) ? null : v],
                    label: { color: or(h.text_colors[i][j], tc),
                             ...(truthy(h.values) && Number.isFinite(v) ? { show: true, formatter: applyFormat(f, v) } : { show: false }) } });
      }
    });
    opt.visualMap = { show: false, min: vmin, max: vmax, inRange: { color: cm } };
    const cticks = tickValues(vmin, vmax, 4).filter(t => vmin - 1e-9 <= t && t <= vmax + 1e-9);
    const cdec = cticks.length ? Math.max(...cticks.map(decimals)) : 0;
    const ctxt = cticks.map(t => fmt(t, `.${Math.min(cdec, 4)}f`));
    const cw = Math.max(...(ctxt.length ? ctxt.map(t => tw(t, fs * 0.85)) : [0]));
    grid.right += 16 + 12 + 6 + cw + 8 + fs * 1.3;
    opt.series.push({ type: "heatmap", name: h.label, data, label: { show: truthy(h.values), fontSize: fs * 0.75, fontFamily: fam },
                      itemStyle: { borderColor: "#ffffff", borderWidth: 0.5 } });
    axisStyle(xa, spec.x, ts, fs, xl, true);
    axisStyle(ya, spec.y, ts, fs, yl, false);
    xa.axisLabel.interval = ya.axisLabel.interval = 0;
    if (model.rotate_x) xa.axisLabel.rotate = model.rotate_x;
    ya.inverse = true;
    if (truthy(spec.y.flip)) ya.inverse = false;
    opt.xAxis = xa;
    opt.yAxis = ya;
    gridFit(grid, xa, ya, h.cols, h.rows, fs, spec);
    opt.grid = { ...grid, containLabel: false };
    delete opt._legend_where;
    const gTop = grid.top, gBot = H - grid.bottom;           // the colour bar beside the plot, as in matplotlib
    const bx = W - grid.right + 16;
    const els: any[] = [{ type: "rect", shape: { x: bx, y: gTop, width: 12, height: gBot - gTop },
                          style: { fill: { type: "linear", x: 0, y: 1, x2: 0, y2: 0,
                                           colorStops: cm.map((c, i) => ({ offset: i / (cm.length - 1), color: c })) },
                                   stroke: "#333333", lineWidth: 0.6 } }];
    cticks.forEach((t, i) => {
      const y = gBot - (t - vmin) / or(vmax - vmin, 1) * (gBot - gTop);
      els.push({ type: "line", shape: { x1: bx + 12, y1: y, x2: bx + 16, y2: y }, style: { stroke: "#333333", lineWidth: 0.8 } });
      els.push({ type: "text", x: bx + 19, y, style: { text: ctxt[i], fill: tc, fontSize: fs * 0.85, fontFamily: fam, verticalAlign: "middle" } });
    });
    els.push({ type: "text", x: bx + 22 + cw + fs * 0.9, y: (gTop + gBot) / 2, rotation: -Math.PI / 2,
               style: { text: h.label, fill: tc, fontSize: fs * 0.9, fontFamily: fam, align: "center", verticalAlign: "middle" } });
    opt.graphic = [{ type: "group", children: els }];
    return [opt, [W, H]];
  }
  if (kind === "bar" || kind === "hbar") {
    const ca: Record<string, any> = { ...catAxis }, va: Record<string, any> = { ...valAxis };
    if (kind === "bar") { xa = ca; ya = va; } else { xa = va; ya = ca; ca.inverse = true; }
    for (const s of model.series) {
      const bt = model.value_labels ? barTexts(model, s) : null;
      const data = (s.y as number[]).map((v, k) => {
        const d: Record<string, any> = { value: !Number.isFinite(v) ? null : v };
        if (truthy(s.bar_colors)) d.itemStyle = { color: s.bar_colors[k] };
        if (bt && bt.length) d.label = { show: !!bt[k], formatter: bt[k] };
        return d;
      });
      const ser: Record<string, any> = { type: "bar", name: s.name, data, itemStyle: { color: s.color }, barGap: "0%", barCategoryGap: "20%" };
      if (model.stack) ser.stack = "total";
      if (model.value_labels) {
        ser.label = { show: true, position: model.stack ? "inside" : kind === "bar" ? "top" : "right", fontSize: fs * 0.8, fontFamily: fam, color: tc };
      }
      opt.series.push(ser);
      if (truthy(s.err)) {
        const e: number[][] = s.err;
        opt.series.push({ type: "custom", name: s.name + " err", renderItem: "__errorbar__" + (kind === "hbar" ? ":h" : ""),
                          data: (s.y as number[]).flatMap((y, k) => Number.isFinite(y) && Number.isFinite(e[0][k]) ? [[k, y - e[0][k], y + e[1][k]]] : []),
                          silent: true, z: 10 });
      }
    }
  } else if (kind === "line") {
    const xt = model.x.type;
    xa = xt === "category" ? { ...catAxis } : { type: xt === "time" ? "time" : "value", scale: true };
    ya = { ...valAxis, scale: true };
    for (const s of model.series) {
      const ys: number[] = s.y;
      let data: any[];
      if (xt !== "category") {
        const xs_: any[] = xt === "time" ? asDays(s.x).map(d => d * 86400e3) : s.x;
        data = xs_.slice(0, ys.length).map((x, i) => [x, !Number.isFinite(ys[i]) ? null : ys[i]]);
      } else data = ys.map(v => !Number.isFinite(v) ? null : v);
      opt.series.push({ type: "line", name: s.name, data, showSymbol: ys.length <= 30, symbolSize: 5 * spec.font_size / 11,
                        lineStyle: { color: s.color, width: (s.width ?? 1.8) * PT, opacity: s.alpha ?? 1.0 },
                        itemStyle: { color: s.color }, connectNulls: false });
    }
  } else if (kind === "scatter") {
    const xt = model.x.type;
    xa = { type: xt === "time" ? "time" : "value", scale: true };
    ya = { ...valAxis, scale: true };
    const ps: number = model.point_size;
    for (const s of model.series) {
      const xs_: any[] = xt === "time" ? asDays(s.x).map(d => d * 86400e3) : s.x;
      opt.series.push({ type: "scatter", name: s.name, data: xs_.slice(0, s.y.length).map((a, i) => [a, s.y[i]]),
                        symbolSize: Math.sqrt(ps) * PT * 1.1, itemStyle: { color: s.color, opacity: model.point_alpha } });
      const t = s.trend;
      if (t) {
        const tx: number[] = t.x;
        const xt_ = xt !== "time" ? tx : tx.map(v => v * 86400e3);
        opt.series.push({ type: "line",
                          name: model.trend_label ? `${s.name} fit: y = ${fmt(t.slope, ".3g")}x + ${fmt(t.intercept, ".3g")}, R² = ${fmt(t.r2, ".2f")}` : s.name + " fit",
                          data: [[xt_[0], t.slope * tx[0] + t.intercept], [xt_[1], t.slope * tx[1] + t.intercept]],
                          showSymbol: false, lineStyle: { color: s.color, type: "dashed", width: 1.4 * PT }, itemStyle: { color: s.color } });
      }
    }
    if (model.trend_label && "legend" in opt) opt.legend.data = opt.series.map((x: any) => x.name);
  } else if (kind === "histogram") {
    const e: number[] = model.edges;
    xa = { type: "value", min: e[0], max: e[e.length - 1], scale: true };
    ya = { ...valAxis };
    const many = model.series.length > 1;
    for (const s of model.series) {
      const data = (s.counts as number[]).map((c, k) => [e[k], e[k + 1], c]);
      opt.series.push({ type: "custom", name: s.name, renderItem: "__histbar__", data,
                        itemStyle: { color: s.color, opacity: many && !model.stack ? 0.55 : 0.9 }, encode: { x: [0, 1], y: 2 }, _stack: model.stack });
    }
    if (model.stack) {
      const acc = new Array<number>(e.length - 1).fill(0);
      for (const ser of opt.series) {
        (ser.data as number[][]).forEach((d, k) => { d.push(acc[k]); acc[k] += d[2]; });
      }
    }
  } else {
    throw new PlotkitError(`unknown chart "${kind}"`);
  }
  // axes
  const [xlab, ylab] = kind !== "hbar" ? [xl, yl] : [yl, xl];
  axisStyle(xa, kind !== "hbar" ? spec.x : spec.y, ts, fs, xlab, true);
  axisStyle(ya, kind !== "hbar" ? spec.y : spec.x, ts, fs, ylab, false);
  if (kind === "hbar" && truthy(spec.x.flip)) ya.inverse = false;
  const lim = model.lims;
  const [vax, vspec] = kind === "hbar" ? [xa, spec.y] : [ya, spec.y];
  if ("v" in lim) {
    const [lo, hi, step] = lim.v;
    if (!("min" in vax)) vax.min = lo;
    if (!("max" in vax)) vax.max = hi;
    if (!truthy(vspec.step) && (vspec.min ?? null) === null && (vspec.max ?? null) === null && !truthy(vspec.log)) vax.interval = step;
  }
  if ("x" in lim) {
    if (!("min" in xa)) xa.min = lim.x[0];
    if (!("max" in xa)) xa.max = lim.x[1];
    if (!truthy(spec.x.step) && (spec.x.min ?? null) === null && (spec.x.max ?? null) === null && !truthy(spec.x.log)) xa.interval = lim.x[2];
  }
  if ("x_tight" in lim) {
    const [lo, hi] = lim.x_tight;
    if (xa.type === "time") {
      if (!("min" in xa)) xa.min = lo * 86400e3;
      if (!("max" in xa)) xa.max = hi * 86400e3;
    } else {
      if (!("min" in xa)) xa.min = lo;
      if (!("max" in xa)) xa.max = hi;
    }
  }
  const tk = or(model.ticks, {});
  for (const [a, which, aspec] of [[xa, "x", kind !== "hbar" ? spec.x : spec.y], [ya, "y", kind !== "hbar" ? spec.y : spec.x]] as const) {
    if (a.type === "category") { a.axisLabel.interval = 0; continue; }
    if (a.type === "time") {
      const xt = or(lim.x_tight, [0, 0]);
      const span = xt[1] - xt[0];
      a.axisLabel.formatter = truthy(span) && span < 2 ? "{HH}:{mm}" : truthy(span) && span < 120 ? "{MM}-{dd}" : "{yyyy}-{MM}";
      continue;
    }
    const isV = (which === "y") !== (kind === "hbar");
    const ticks: number[] | undefined = isV ? tk.v : tk.x;
    if (truthy(ticks) && !truthy(aspec.step) && !truthy(aspec.log) && (aspec.min ?? null) === null && (aspec.max ?? null) === null) {
      a.axisLabel.customValues = ticks;
      a.axisTick.customValues = ticks;
      delete a.interval;
      const dec = Math.max(...ticks!.map(decimals));
      a.axisLabel.formatter = "__fmt__{:." + String(Math.min(dec, 6)) + "f}";
    } else if (!truthy(a.axisLabel.formatter)) {
      a.axisLabel.formatter = "__fmt__{:.10g}";          // 1190, not 1,190
    }
  }
  if (model.rotate_x && xa.type === "category") xa.axisLabel.rotate = model.rotate_x;
  opt.xAxis = xa;
  opt.yAxis = ya;
  gridFit(grid, xa, ya, or(xa.data, []), or(ya.data, []), fs, spec);
  opt.grid = { ...grid, containLabel: false };
  placeLegend(opt, grid);
  for (const r of model.refs) {
    const vertical = (r.axis === "x") !== (kind === "hbar");
    const item: Record<string, any> = { [vertical ? "xAxis" : "yAxis"]: r.value };
    item.label = truthy(r.text) ? { show: true, formatter: r.text, position: "insideEndTop", color: r.color, fontSize: fs * 0.85, fontFamily: fam }
      : { show: false };
    let tgt = opt.series.find((x: any) => ["bar", "line", "scatter"].includes(x.type));
    if (tgt === undefined) {
      tgt = { type: "line", data: [], name: "_ref" };
      opt.series.push(tgt);
    }
    if (!("markLine" in tgt)) tgt.markLine = { silent: true, symbol: "none", data: [] };
    tgt.markLine.data.push({ ...item, lineStyle: { color: r.color, type: echartsDash(r.style, 1.2 * PT), width: 1.2 * PT } });
  }
  if (truthy(spec.grid)) {
    const a = kind !== "hbar" ? ya : xa;
    if (!("splitLine" in a)) a.splitLine = {};
    a.splitLine.show = true;
  }
  if (truthy(opt._legend_dummy)) {
    const name = opt._legend_dummy;
    delete opt._legend_dummy;
    opt.series.push({ type: "line", name, data: [], silent: true });
  }
  return [opt, [W, H]];
}

/** A legend inside the plot goes in the chosen corner of the grid. */
function placeLegend(opt: EChartsOption, grid: Record<string, number>): void {
  const w = opt._legend_where;
  delete opt._legend_where;
  const leg = opt.legend;
  if (!truthy(leg) || w === undefined || w === null || String(w).startsWith("outside")) return;
  const vpos = w.includes("upper") ? "top" : w.includes("lower") ? "bottom" : "middle";
  const hpos = w.includes("left") ? "left" : ["upper center", "lower center", "center"].includes(w) ? "center" : "right";
  if (vpos === "top") leg.top = grid.top + 6;
  else if (vpos === "bottom") leg.bottom = grid.bottom + 6;
  else leg.top = "middle";
  if (hpos === "center") leg.left = "center";
  else if (hpos === "left") leg.left = grid.left + 8;
  else leg.right = grid.right + 8;
}

function axisStyle(a: Record<string, any>, s: Record<string, any>, ts: Record<string, any>, fs: number, label: string, horizontal: boolean): void {
  a.name = label;
  a.nameLocation = "middle";
  a.nameTextStyle = { ...ts, fontSize: or(or(s.label_size, 0) * PT, fs) };
  const { fontSize: _, ...rest } = ts;
  a.axisLabel = { ...rest, fontSize: or(or(s.tick_size, 0) * PT, fs), hideOverlap: false };
  a.axisLine = { show: true, onZero: false, lineStyle: { color: "#333333" } };
  a.axisTick = { show: true, inside: true, alignWithLabel: true };
  a.splitLine = { show: false };
  if (["value", "time", "log"].includes(a.type) || a.type === undefined || a.type === null) {
    for (const k of ["min", "max"]) {
      if (s[k] !== null && s[k] !== undefined) {
        let v = s[k];
        if (a.type === "time" && typeof v === "string") v = asDays([v])[0] * 86400e3;   // the data is UTC milliseconds too
        a[k] = v;
      }
    }
    if (truthy(s.step)) a.interval = specNum(s.step, "step");
    if (truthy(s.log)) a.type = "log";
    if (truthy(s.format)) a.axisLabel.formatter = "__fmt__" + s.format;
  }
  if (truthy(s.flip)) a.inverse = !truthy(a.inverse ?? false);
  if (s.rotate !== null && s.rotate !== undefined && horizontal) a.axisLabel.rotate = specNum(s.rotate, "rotate");
}

/** Margins from estimated label sizes (SSR has no text metrics). */
function gridFit(grid: Record<string, number>, xa: Record<string, any>, ya: Record<string, any>, xcats: unknown[], ycats: unknown[],
                 fs: number, spec: ChartSpec): void {
  let ylabW = amax(ycats.length ? ycats.map(c => tw(c, fs)) : [tw("0000.0", fs)]);
  if (ya.type === "value" || ya.type === "log") ylabW = tw("00000", fs);
  let rot = (xa.axisLabel ?? {}).rotate ?? null;
  const longest = amax(xcats.length ? xcats.map(c => tw(c, fs)) : [0]);
  if (rot === null && xcats.length && xcats.reduce((acc: number, c) => acc + (tw(c, fs) + 8), 0) > (spec.size[0] * 96 - ylabW - 80) * 0.95) {
    xa.axisLabel.rotate = 45;
    rot = 45;
  }
  const xlabH = fs * 1.2 + (truthy(rot) ? longest * Math.sin(Number(rot) * (Math.PI / 180)) : 0);
  const hasY = truthy(ya.name), hasX = truthy(xa.name);
  grid.left += ylabW + 14 + (hasY ? fs * 1.6 : 0);
  ya.nameGap = ylabW + 10;
  grid.bottom += xlabH + 10 + (hasX ? fs * 1.6 : 0);
  xa.nameGap = xlabH + 8;
  grid.right += 18;
  grid.top += 4;
}

/** _merge: b over a, dicts key by key and lists item by item. */
export function mergeOption(a: any, b: any): any {
  if (isDict(a) && isDict(b)) {
    const out: Record<string, any> = { ...a };
    for (const [k, v] of Object.entries(b)) out[k] = k in a ? mergeOption(a[k], v) : v;
    return out;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    return [...a.map((x, i) => i < b.length ? mergeOption(x, b[i]) : x), ...b.slice(a.length)];
  }
  return b;
}

function isDict(v: unknown): v is Record<string, any> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

/** The spec's "echarts" patch, checked (validatePatch: plotkit.echarts.validate_patch's port) and merged over opt. */
export function applyPatch(spec: ChartSpec, opt: EChartsOption, validatePatch?: ValidatePatch): EChartsOption {
  if (!truthy(spec.echarts)) return opt;
  let patch: Record<string, any>;
  if (validatePatch) patch = validatePatch(spec.echarts);
  else {                                                // unchecked: only the shape validate_patch gives
    patch = structuredClone(typeof spec.echarts === "string" ? JSON.parse(spec.echarts) : spec.echarts);
    for (const k of ["yAxis", "series", "graphic"]) if (k in patch && !Array.isArray(patch[k])) patch[k] = [patch[k]];
  }
  for (const k of ["xAxis", "yAxis"]) {                 // one axis each here; the patch may give a list
    if (Array.isArray(patch[k])) patch[k] = patch[k].length ? patch[k][0] : {};
  }
  return mergeOption(opt, patch);
}

/** The chart as an ECharts option for a live chart (tooltip, zoom), in the shared result shape with "options" and
 *  nothing saved (plotkit.charts.live_result, from a normalized spec and its loaded table). Number formats and custom
 *  series stay "__fmt__..." / "__histbar__" / "__errorbar__" markers: revive() turns them into functions. */
export function liveResult(spec: ChartSpec, frame: Frame, validatePatch?: ValidatePatch): ChartResult {
  if (truthy(spec.code)) {
    throw new PlotkitError('"code" only works with the matplotlib engine',
      'use "data_code" for data changes (both engines), or an "echarts" patch for drawing changes');
  }
  const model = layout(spec, buildModel(spec, frame));
  const [opt0] = echartsOption(spec, model, true);
  const opt = applyPatch(spec, opt0, validatePatch);
  return { ok: true, kind: "chart", engine: "echarts", options: [opt], saved: [], warnings: [...model.notes],
           not_done: notDone(spec), values: summaryValues(model), chart: model.kind, rows_used: model.rows_used,
           rows_total: model.rows_total };
}

const r4 = (v: number) => pyRound(v, 4);

/** The numbers reported back with a chart (plotkit.charts.summary_values). */
export function summaryValues(model: ChartModel): Record<string, any> {
  const k = model.kind;
  if (k === "pie") {
    const p = model.pie;
    const slices: Record<string, number> = {}, shares: Record<string, number> = {};
    (p.labels as string[]).forEach((l, i) => { slices[l] = r4(p.values[i]); });
    (p.labels as string[]).forEach((l, i) => { shares[l] = r4(p.shares[i]); });
    return { slices, shares };
  }
  if (k === "heatmap") {
    const h = model.heat;
    const z: number[][] = h.z;
    let bi = -1, bj = -1;
    z.forEach((row, i) => row.forEach((v, j) => { if (!Number.isNaN(v) && (bi < 0 || v > z[bi][bj])) { bi = i; bj = j; } }));
    if (!z.some(row => row.some(Number.isFinite))) return {};
    return { rows: h.rows, cols: h.cols, max: { row: h.rows[bi], col: h.cols[bj], value: r4(z[bi][bj]) } };
  }
  if (k === "histogram") {
    const series: Record<string, any> = {};
    for (const s of model.series) series[s.name] = { n: s.n, mean: s.mean };
    return { bins: model.edges.length - 1, series };
  }
  if (k === "bar" || k === "hbar") {
    const series: Record<string, any> = {};
    for (const s of model.series) series[s.name] = (s.y as number[]).map(v => !Number.isFinite(v) ? null : r4(v));
    return { categories: model.x.categories, series };
  }
  if (k === "line") {
    const series: Record<string, any> = {};
    for (const s of model.series) series[s.name] = { n: s.y.length, min: nanr(nanMin(s.y)), max: nanr(nanMax(s.y)) };
    return { series };
  }
  if (k === "scatter") {
    const series: Record<string, any> = {};
    for (const s of model.series) {
      series[s.name] = { n: s.y.length, ...(s.trend ? { slope: pyRound(s.trend.slope, 5), r2: r4(s.trend.r2) } : {}) };
    }
    return { series };
  }
  return {};
}

/** The entries of a values dict in Python's order (the model's): JS objects put integer-like keys first. */
function inOrder(keys: string[], obj: Record<string, any>): [string, any][] {
  return [...new Set(keys)].filter(k => Object.hasOwn(obj, k)).map(k => [k, obj[k]]);
}

function nanr(v: number | null | undefined): number | null {
  return v === null || v === undefined || !Number.isFinite(v) ? null : r4(v);
}

/** What was drawn, in Korean, from the numbers (plotkit.charts.korean_summary). paths: the saved file names. */
export function koreanSummary(model: ChartModel, values: Record<string, any>, paths: string[], notDoneList: string[], warnings: string[]): string {
  const k = model.kind;
  const names: string[] = model.series.map((s: any) => s.name);
  const lines = [`${KIND_KO[k]} 그래프를 저장했습니다: ${paths.map(p => p.split(/[\\/]/).pop()).join(", ")}`];
  lines.push(`사용한 행: ${model.rows_used} / ${model.rows_total}`);
  if (k === "bar" || k === "hbar") {
    const cats: string[] = model.x.categories;
    for (const s of model.series.slice(0, 4)) {
      const pairs = cats.flatMap((c, i) => i < s.y.length && Number.isFinite(s.y[i]) ? [`${c} ${fmt(s.y[i], ".3g")}`] : []).slice(0, 8);
      lines.push(`${s.name}: ` + pairs.join(", ") + (cats.length > 8 ? " …" : ""));
    }
  } else if (k === "pie") {
    lines.push(inOrder(model.pie.labels, values.shares).slice(0, 8).map(([l, s]) => `${l} ${fmt(s * 100, ".1f")}%`).join(", "));
  } else if (k === "heatmap" && truthy(values)) {
    const m = values.max;
    lines.push(`가장 큰 값: ${m.row} / ${m.col} = ${fmt(m.value, ".4g")}`);
  } else if (k === "scatter") {
    for (const [n, d] of inOrder(names, values.series)) {
      lines.push(`${n}: ${d.n}점` + ("slope" in d ? `, 기울기 ${fmt(d.slope, ".3g")}, R² ${fmt(d.r2, ".2f")}` : ""));
    }
  } else if (k === "line") {
    for (const [n, d] of inOrder(names, values.series).slice(0, 6)) {
      lines.push(d.min !== null ? `${n}: ${d.n}점, ${fmt(d.min, ".4g")} ~ ${fmt(d.max, ".4g")}` : `${n}: 값 없음`);
    }
  } else if (k === "histogram") {
    for (const [n, d] of inOrder(names, values.series)) {
      lines.push(d.mean !== null ? `${n}: ${d.n}개, 평균 ${fmt(d.mean, ".4g")}` : `${n}: 값 없음`);
    }
  }
  for (const r of model.refs) if (truthy(r.text)) lines.push(`기준선: ${specStr(r.text)}`);
  if (notDoneList.length) lines.push("처리하지 못한 요청: " + notDoneList.join("; "));
  for (const w of warnings) lines.push(`참고: ${w}`);
  return lines.join("\n");
}

