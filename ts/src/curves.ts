// Curves on the ECharts engine: a normalized curve spec and its data jobs -> engine-neutral "resolved figures"
// (numbers, colours, texts and tick positions), the same dicts as plotkit.echarts.resolve, and the shared result of
// a live chart (plotkit.echarts.live_result). Also the curve helpers of plotkit.core both engines share: label
// templates, titles, series colours and names, axis labels and units, not_done and the values the labels report.
//
// The normalized spec (plotkit.core.normalize_spec, with its internal "_" keys) and the jobs (plotkit.core.build_jobs:
// one per sheet, data arrays already finite and flipped) come from the other modules; this one reads them only
// (resolve adds "colors" to each job, as Python does).
import { toHex, toRgb } from "./colors.ts";
import { PlotkitError } from "./errors.ts";
import { formatValue, pyDivmod, pyFormat, PyFormatError, PyInt, pyRepr, pyRound } from "./pyfmt.ts";
import { COMBINE_COLORS } from "./tables.ts";
import { tickValues } from "./ticks.ts";
import { findPeaksXY, valueAtX } from "./peaks.ts";
import { liveOptions } from "./live.ts";

export const SMALL = 0.833;                // matplotlib's "small" font size factor

/* eslint-disable @typescript-eslint/no-explicit-any */
type Dict = Record<string, any>;

/** One axis of a normalized curve spec (plotkit.core.DEFAULTS["x" | "y1" | "y2"] merged with the preset and the
 *  user's keys). Keys can be missing (y2 switched off is {"show": false}). */
export interface AxisSpec {
  col?: unknown; label?: unknown; min?: number | null; max?: number | null; step?: number | null;
  color?: string | null; width?: number | null; linestyle?: string; style?: string; flip?: string; log?: unknown;
  legend?: string | null; show?: unknown; label_size?: number | null; label_color?: string | null;
  tick_size?: number | null; tick_color?: string | null; minor?: unknown; invert?: unknown; _preset_label?: boolean;
  [k: string]: unknown;
}

/** One entry of spec.annotate (or a data_code mark). */
export interface AnnotSpec {
  type: string; on?: string; x?: number | null; y?: number | null; method?: string; text?: string | null;
  color?: string | null; size?: number | null; count?: number; kind?: string; x_min?: number | null;
  x_max?: number | null; min_rel?: number | null; alpha?: number | null; linestyle?: string; where?: string;
  _preset_text?: boolean; _requested?: boolean;
  [k: string]: unknown;
}

/** A normalized curve spec (plotkit.core.normalize_spec), with its internal keys (_text_color_set, ...). */
export interface CurveSpec {
  file: string[];
  x: AxisSpec; y1: AxisSpec; y2: AxisSpec;
  annotate: Record<string, AnnotSpec>;
  title: { text?: string | null; size?: number | null; color?: string | null };
  legend: { where: string; show: unknown; size: number | null };
  text_color: string; tick_direction: string; echarts: Dict | null; grid: unknown; size: unknown[]; dpi: unknown;
  font: unknown; font_size: number; combine: unknown; colors: string[] | null; names: unknown[] | null;
  panels: string | null; asks?: unknown[]; output?: { dir?: string | null; format?: string[]; name?: string | null };
  _text_color_set: boolean;
  [k: string]: unknown;
}

/** A column a job uses: its letter, 0-based index and header name. */
export interface JobColumn { letter: string; index: number; name: string; [k: string]: unknown }

/** One sheet to draw (plotkit.core.build_jobs). data holds finite numbers per role (x, y1 and maybe y2). */
export interface Job {
  file: string; sheet: string; cols: Record<string, JobColumn>; how: string;
  data: Record<string, ArrayLike<number>>; rows: number; marks?: Record<string, AnnotSpec>; yoff?: number;
  colors?: { y1: string; y2: string };
  [k: string]: unknown;
}

export interface FigureAxis {
  label: string; label_size: number; label_color: string; tick_size: number; tick_color: string;
  tick_mark_color: string; line_color: string | null; min: number; max: number; ticks: number[] | null;
  log: boolean; inverse: boolean; minor: boolean;
}

export interface FigureSeries {
  axis: "y1" | "y2"; name: string; sheet: string; color: string; width: number; linestyle: string; style: string;
  points: [number, number][];
}

/** A label, marker, line, band or text of a figure (the fields depend on kind). */
export interface FigureAnnotation {
  kind: "value" | "note" | "peak" | "vline" | "hline" | "band" | "text_at" | "text";
  name: string; axis?: "y1" | "y2"; x?: number; y?: number; value?: number; text: string; color?: string;
  text_color?: string; size: number; stack?: number; down?: boolean; linestyle?: string; x_min?: number;
  x_max?: number; fill?: string; where?: string;
}

/** A resolved figure (plotkit.echarts.resolve): everything the ECharts side needs, nothing engine-specific. */
export interface Figure {
  size_in: number[]; dpi: number; font_family: string; font_size: number; text_color: string;
  title: { text: string; size: number; color: string };
  tick_direction: string; grid: boolean;
  axes: { x: FigureAxis; y1: FigureAxis; y2: FigureAxis | null };
  series: FigureSeries[]; series_index: string;
  legend: { show: boolean; where: string; size: number; names: string[]; extra: { name: string; color: string; linestyle: string }[]; color: string };
  annotations: FigureAnnotation[]; box_peaks: boolean; panels: "split" | null; echarts: Dict | null;
  n_series?: number;
  [k: string]: unknown;
}

/** What a label reports (one entry per annotation and sheet), as plotkit.echarts._annotations appends them. */
export type AnnotationResult = Dict & { name: string; sheet: string };

export interface Resolved { group: Job[]; figure: Figure; annotations: AnnotationResult[] }

// =================================================================== Python semantics
/** Python's truth value (empty strings, lists and dicts, 0 and None are false; NaN is true). */
export function truthy(v: unknown): boolean {
  if (v === null || v === undefined || v === false || v === "" || v === 0) return false;
  if (v instanceof PyInt) return v.value !== 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v as object).length > 0;
  return true;
}

/** Python's a or b. */
function or<A, B>(a: A, b: B): A | B {
  return truthy(a) ? a : b;
}

/** dict.get(key, default): the default only when the key is missing (a None value stays None). */
function get<T = any>(d: any, key: string, dflt: T = null as T): T {
  return d != null && Object.hasOwn(d, key) ? d[key] : dflt;
}

/** Python's repr() of a str. */
export function reprStr(s: string): string {
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    const cp = ch.codePointAt(0)!;
    if (ch === quote || ch === "\\") out += "\\" + ch;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (ch !== " " && /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u.test(ch)) {
      out += cp < 0x100 ? "\\x" + cp.toString(16).padStart(2, "0") : cp < 0x10000 ? "\\u" + cp.toString(16).padStart(4, "0")
        : "\\U" + cp.toString(16).padStart(8, "0");
    } else out += ch;
  }
  return out + quote;
}

/** Python's str() of a JSON value: whole numbers read as Python ints (JSON loses 1 vs 1.0), lists and dicts as repr. */
export function pyStrValue(v: unknown): string {
  if (typeof v === "string") return v;
  return pyReprValue(v);
}

function pyReprValue(v: unknown): string {
  if (v instanceof PyInt) return String(v.value);
  if (typeof v === "number") return Number.isInteger(v) && Math.abs(v) < 1e16 ? String(v) : pyRepr(v);
  if (typeof v === "string") return reprStr(v);
  if (v === null || v === undefined) return "None";
  if (typeof v === "boolean") return v ? "True" : "False";
  if (Array.isArray(v)) return "[" + v.map(pyReprValue).join(", ") + "]";
  if (typeof v === "object") return "{" + Object.entries(v as object).map(([k, x]) => `${reprStr(k)}: ${pyReprValue(x)}`).join(", ") + "}";
  return String(v);
}

/** Python's float() of a value (numbers, bools, numeric strings). */
function pyFloat(v: unknown): number {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  if (v instanceof PyInt) return v.value;
  if (typeof v === "string") {
    const s = v.trim().replace(/(?<=\d)_(?=\d)/g, "");
    if (/^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(s)) return parseFloat(s);
    const m = /^([+-]?)(inf|infinity|nan)$/i.exec(s);
    if (m) return m[2].toLowerCase() === "nan" ? NaN : m[1] === "-" ? -Infinity : Infinity;
  }
  throw new Error(`could not convert string to float: ${pyReprValue(v)}`);
}

/** str.replace(old, new) for every occurrence, without JavaScript's "$" patterns. */
function replaceAll(s: string, a: string, b: string): string {
  return s.split(a).join(b);
}

/** pathlib's PurePosixPath(p).name / .stem (Python 3.13). */
function pathName(p: string): string {
  const parts = String(p).split("/").filter(x => x !== "" && x !== ".");
  return parts.length ? parts[parts.length - 1] : "";
}

export function pathStem(p: string): string {
  const name = pathName(p);
  const i = name.lastIndexOf(".");
  return i > 0 && i < name.length - 1 ? name.slice(0, i) : name;
}

function nanMin(arrays: ArrayLike<number>[]): number {
  let m = NaN;
  for (const a of arrays) for (let i = 0; i < a.length; i++) { const v = a[i]; if (!Number.isNaN(v) && !(v >= m)) m = v; }
  return m;
}

function nanMax(arrays: ArrayLike<number>[]): number {
  let m = NaN;
  for (const a of arrays) for (let i = 0; i < a.length; i++) { const v = a[i]; if (!Number.isNaN(v) && !(v <= m)) m = v; }
  return m;
}

// =================================================================== plotkit.core helpers
/** plotkit.core._fmt: fill a label template. {} gets the main value (x as "{:.0f}", y as "{:.1f}"); {x} and {y}
 *  are numbers with any format spec. */
export function fmt(text: unknown, x: number | null, y: number | null, primary: "x" | "y"): string {
  if (text === null || text === undefined) return "";
  let t = typeof text === "string" ? text : pyStrValue(text);
  if (t.includes("{}")) {
    const pv = primary === "x" ? x : y;
    t = replaceAll(t, "{}", formatValue(pv, primary === "x" ? ".0f" : ".1f"));
  }
  try {
    return pyFormat(t, [], { x: x ?? NaN, y: y ?? NaN });
  } catch (e) {
    if (e instanceof PyFormatError) {
      throw new PlotkitError(`label template ${typeof text === "string" ? reprStr(text) : pyReprValue(text)} is invalid (${formatErrorText(t, e.message)})`,
        'use {x}, {y} or {}, e.g. "Residue {y:.1f}%"');
    }
    throw e;
  }
}

/** Python's error text where pyFormat's differs: it says "Single '{' ..." for any field without a closing brace (Python
 *  only when the "{" is the last character, else "expected '}' before end of string"), and "Invalid format specifier"
 *  for every spec it can not parse (see floatSpecError). */
function formatErrorText(t: string, message: string): string {
  const bad = /^Invalid format specifier '([\s\S]*)'$/.exec(message);
  if (bad) return floatSpecError(bad[1]);
  if (message !== "Single '{' encountered in format string") return message;
  let i = 0;
  while (i < t.length) {                     // walk the template as pyFormat does, to the "{" it failed on
    if (t[i] === "{") {
      if (t[i + 1] === "{") { i += 2; continue; }
      const end = t.indexOf("}", i);
      if (end < 0) return i === t.length - 1 ? message : "expected '}' before end of string";
      i = end + 1;
    } else i += t[i] === "}" && t[i + 1] === "}" ? 2 : 1;
  }
  return message;
}

/** Python's message for a format spec pyFormat rejects, on a float (CPython's parse_internal_render_format_spec, then
 *  format_float_internal); pyFormat says "Invalid format specifier '...'" for all of them. */
function floatSpecError(spec: string): string {
  const ch = Array.from(spec);
  let pos = 0, fill = false, sep = "";
  const isAlign = (c: string | undefined) => c !== undefined && "<>=^".includes(c);
  if (ch.length - pos >= 2 && isAlign(ch[pos + 1])) { fill = true; pos += 2; }
  else if (ch.length - pos >= 1 && isAlign(ch[pos])) pos++;
  if (pos < ch.length && "+- ".includes(ch[pos])) pos++;
  if (pos < ch.length && ch[pos] === "z") pos++;
  if (pos < ch.length && ch[pos] === "#") pos++;
  if (!fill && pos < ch.length && ch[pos] === "0") pos++;
  while (pos < ch.length && /\d/.test(ch[pos])) pos++;
  if (pos < ch.length && ch[pos] === ",") { sep = ","; pos++; }
  if (pos < ch.length && ch[pos] === "_") {
    if (sep) return "Cannot specify both ',' and '_'.";
    sep = "_"; pos++;
  }
  if (pos < ch.length && ch[pos] === "," && sep === "_") return "Cannot specify both ',' and '_'.";
  if (pos < ch.length && ch[pos] === ".") {
    pos++;
    const p0 = pos;
    while (pos < ch.length && /\d/.test(ch[pos])) pos++;
    if (pos === p0) return "Format specifier missing precision";
  }
  if (ch.length - pos > 1) return `Invalid format specifier '${spec}' for object of type 'float'`;
  const type = ch[pos] ?? "";
  if (sep && !"defgEG%F".includes(type || "d")) {
    return `Cannot specify '${sep}' with '${type}'.`;
  }
  if (!"eEfFgGn%".includes(type || "g")) return `Unknown format code '${type}' for object of type 'float'`;
  return `Invalid format specifier '${spec}' for object of type 'float'`;
}

/** plotkit.core._unit: the unit in brackets at the end of a name: "Weight (mg)" -> "mg", "D.W(%/C)" -> "%/C". */
export function unit(name: string | null | undefined): string | null {
  const m = /[(\[]\s*([^()\[\]]+?)\s*[)\]]\s*$/.exec(name || "");
  return m ? m[1] : null;
}

/** plotkit.core._same_unit: equal ignoring case, spaces and degree signs ("°C" = "C" = "℃"). */
export function sameUnit(a: string, b: string): boolean {
  const norm = (u: string) => replaceAll(u.toLowerCase(), "℃", "c").replace(/[\s°]/g, "");
  return norm(a) === norm(b);
}

/** plotkit.core._labels: an axis label: the spec's, else the column's name; a preset label gives way to the column
 *  name when their units differ. */
export function labels(spec: CurveSpec, role: "x" | "y1" | "y2", col: JobColumn): string {
  let lab = get<any>(spec[role], "label");
  if (lab === null || lab === undefined) {
    lab = or(col.name, `column ${col.letter}`);
  } else if (truthy(get(spec[role], "_preset_label"))) {
    const mine = unit(lab), theirs = unit(col.name);
    if (mine && theirs && !sameUnit(mine, theirs)) lab = col.name;
  }
  return lab;
}

/** plotkit.core.figure_title: the title template with {sheet} and {file} (no title for combined sheets by default). */
export function figureTitle(spec: CurveSpec, first: Job): string {
  let tpl: string = or(get(spec.title, "text"), "");
  if (truthy(spec.combine) && tpl === "{sheet}") tpl = "";
  return replaceAll(replaceAll(tpl, "{sheet}", first.sheet), "{file}", pathStem(first.file));
}

/** plotkit.core.file_stem: the output file name (no extension) for a figure. */
export function fileStem(nameTpl: string, spec: CurveSpec, first: Job): string {
  const fname = replaceAll(replaceAll(nameTpl, "{sheet}", truthy(spec.combine) ? "all_sheets" : first.sheet), "{file}", pathStem(first.file));
  return fname.replace(/[\\/:*?"<>|\s]+/g, "_").replace(/^_+|_+$/g, "") || "plot";
}

/** plotkit.core.series_style: (y1 colour, y2 colour, legend name) of sheet k. */
export function seriesStyle(spec: CurveSpec, j: Job, k: number): [string, string, string] {
  let c1: string, c2: string, lab1: string;
  const names = (or(get(spec, "names"), []) as unknown[]);
  if (truthy(spec.combine)) {
    const cols = or(get(spec, "colors"), COMBINE_COLORS as unknown as string[]) as string[];
    c1 = cols[((k % cols.length) + cols.length) % cols.length];
    c2 = c1;
    if (k < names.length) lab1 = pyStrValue(names[k]);
    else if (spec.file.length === 1) lab1 = j.sheet;
    else lab1 = new Set(spec.file.map(pathStem)).size > 1 ? pathStem(j.file) : j.sheet;
  } else {
    const cols = or(get(spec, "colors"), []) as string[];
    c1 = cols.length ? cols[0] : (spec.y1.color as string);
    c2 = cols.length > 1 ? cols[1] : (spec.y2.color as string);
    lab1 = names.length ? pyStrValue(names[0]) : or(get(spec.y1, "legend"), labels(spec, "y1", j.cols.y1)) as string;
  }
  return [c1, c2, lab1];
}

/** plotkit.core.not_done: the asks the model marked unsupported. */
export function notDone(spec: { asks?: unknown[] | unknown; [k: string]: unknown }): string[] {
  const asks = or(get(spec, "asks"), []) as unknown[];
  const out: string[] = [];
  for (const a of asks) {
    if (!a || typeof a !== "object" || Array.isArray(a)) continue;
    if (["unsupported", "no", "none", "not_done"].includes(pyStrValue(get(a, "how", "")).toLowerCase())) out.push(pyStrValue(get(a, "ask", "")));
  }
  return out;
}

/** plotkit.core.curve_values: the numbers the labels show, per sheet: {sheet: {name: {"x", "value"} | [peaks]}}. */
export function curveValues(plots: { annotations: AnnotationResult[] }[]): Record<string, Record<string, unknown>> {
  const out: Record<string, Record<string, unknown>> = {};
  for (const r of plots) {
    for (const a of r.annotations) {
      if (Object.hasOwn(a, "peaks")) {
        (out[a.sheet] ??= {})[a.name] = (a.peaks as Dict[]).map(p => ({ ...p }));
      } else if (Object.hasOwn(a, "value")) {
        (out[a.sheet] ??= {})[a.name] = { x: get(a, "x_used", get(a, "x")), value: a.value };
      }
    }
  }
  return out;
}

// =================================================================== plotkit.echarts
/** plotkit.echarts._hex: "#rrggbb". */
export function hex(c: unknown): string {
  return toHex(c);
}

/** plotkit.echarts._rgba: "rgba(r,g,b,alpha)". */
export function rgba(c: unknown, alpha: number): string {
  const [r, g, b] = toRgb(c).map(v => pyRound(255 * v));
  return `rgba(${r},${g},${b},${formatValue(alpha, "g")})`;
}

/** plotkit.echarts._clean: a float rounded to 10 significant digits (as JSON writes it). */
export function clean(v: unknown): number {
  const x = pyFloat(v);
  if (!Number.isFinite(x)) return x;
  return parseFloat(formatValue(x, ".10g"));
}

/** plotkit.echarts._ticks: the tick values inside [lo, hi] matplotlib would pick (null on a log axis). */
export function ticks(lo: number, hi: number, axspec: AxisSpec): number[] | null {
  if (truthy(get(axspec, "log"))) return null;
  const step = get<number | null>(axspec, "step");
  let vals: number[];
  if (truthy(step)) {
    const s = step as number;
    const off = get(axspec, "min") !== null ? pyDivmod(axspec.min as number, s)[1] : 0.0;
    const k0 = Math.ceil((lo - off) / s - 1e-9);
    const stop = Math.floor((hi - off) / s + 1e-9) + 1;
    vals = [];
    for (let k = k0; k < stop; k++) vals.push(off + s * k);
  } else {
    const tol = 1e-9 * Math.abs(hi - lo);
    vals = tickValues(lo, hi, "auto").filter(v => v >= lo - tol && v <= hi + tol);
    if (vals.length > 9) vals = tickValues(lo, hi, 7).filter(v => v >= lo && v <= hi);
  }
  return vals.map(clean);
}

/** plotkit.echarts._axis_range: [min, max, ticks], the limits plotkit._apply_axis sets. */
export function axisRange(axspec: AxisSpec, dataMin: number, dataMax: number, padLo: number, padHi: number,
  tight = false): [number, number, number[] | null] {
  let lo = get<number | null>(axspec, "min"), hi = get<number | null>(axspec, "max");
  const rng = or(dataMax - dataMin, 1.0);
  if (lo === null) lo = tight ? dataMin : dataMin - padLo * rng;
  if (hi === null) hi = tight ? dataMax : dataMax + padHi * rng;
  if (hi <= lo) throw new PlotkitError(`axis range is empty (min ${pyRepr(lo)} >= max ${pyRepr(hi)})`);     // floats in Python
  const step = get<number | null>(axspec, "step");
  if (truthy(step) && !truthy(get(axspec, "log")) && (hi - lo) / (step as number) > 60) {
    throw new PlotkitError(`step ${pyRepr(step as number)} is too small for range ${formatValue(lo, "g")}..${formatValue(hi, "g")}`, "use a larger step");
  }
  return [clean(lo), clean(hi), ticks(lo, hi, axspec)];
}

const KOREAN = /[가-힣ㄱ-ㆎ]/;

/** plotkit.echarts._font_family: the spec's font, else a Korean-capable list when any text is Korean. */
export function fontFamily(spec: CurveSpec, texts: unknown[]): string {
  if (truthy(spec.font)) return `${pyStrValue(spec.font)}, sans-serif`;
  const korean = texts.some(t => KOREAN.test(String(or(t, ""))));
  if (korean) {
    return "Malgun Gothic, Apple SD Gothic Neo, AppleGothic, NanumGothic, Noto Sans CJK KR, " +
      "Noto Sans KR, WenQuanYi Zen Hei, sans-serif";
  }
  return "DejaVu Sans, Arial, Helvetica, sans-serif";
}

/** plotkit.echarts._annotations: the labels of one sheet as data (appends what they report to results). */
export function annotations(spec: CurveSpec, axesOn: string[], j: Job, colors: Record<string, string>,
  results: AnnotationResult[], stack: number, combineColor: string | null, textAll: boolean): FigureAnnotation[] {
  const out: FigureAnnotation[] = [];
  const tc = spec.text_color;
  const base = spec.font_size;
  const yoff = get<number>(j, "yoff", 0.0);
  const entries = [...Object.entries(spec.annotate), ...Object.entries(get<Record<string, AnnotSpec>>(j, "marks", {}))];
  for (const [name, a] of entries) {
    const t = a.type;
    const on = get<string>(a, "on", "y1");
    const sheet = j.sheet;
    if ((t === "value_at_x" || t === "peak" || t === "hline") && !axesOn.includes(on)) {
      results.push({ name, sheet, skipped: `${on} is not drawn` });
      continue;
    }
    const ax = (axesOn.includes(on) ? on : "y1") as "y1" | "y2";
    const col = or(or(get(a, "color"), combineColor), Object.hasOwn(colors, on) ? colors[on] : tc) as string;
    const tcol = textAll && !truthy(get(a, "color")) ? tc : col;
    const fs = or(get(a, "size"), base * SMALL) as number;
    const data = j.data;
    if (t === "value_at_x") {
      const X = data.x, Y = data[on];
      const [xu, yv] = valueAtX(X, Y, a.x as number, get(a, "method", "nearest"));
      if (xu === null) {
        results.push({ name, sheet, x: a.x, value: null,
          note: `x=${formatValue(a.x, "g")} is outside the data (${formatValue(nanMin([X]), ".0f")}..${formatValue(nanMax([X]), ".0f")})` });
        if (truthy(get(a, "_requested"))) {
          out.push({ kind: "note", name, axis: ax, stack,
            text: `${name}: no data at x = ${formatValue(a.x, "g")}\n(data ends at ${formatValue(nanMax([X]), ".0f")})`,
            color: hex(textAll ? tc : or(combineColor, "gray")), size: base * SMALL });
        }
        continue;
      }
      let text = get<any>(a, "text", "{y:.1f}");
      const u = Object.hasOwn(j.cols, on) ? unit(j.cols[on].name) : null;
      if (truthy(get(a, "_preset_text")) && u && !sameUnit(u, "%")) text = replaceAll(text, "{y:.1f}%", "{y:.3g} " + u);
      const shown = yv - (on === "y1" ? yoff : 0.0);          // offset curves keep their real values
      const label = fmt(text, xu, shown, "y");
      out.push({ kind: "value", name, axis: ax, x: clean(xu), y: clean(yv), text: label, color: hex(col),
        text_color: hex(tcol), size: fs, stack });
      results.push({ name, sheet, x_requested: a.x, x_used: pyRound(xu, 3), value: pyRound(shown, 4), text: label });
    } else if (t === "peak") {
      const kind = get<string>(a, "kind", "max");
      const peaks = findPeaksXY(data.x, data[on], get(a, "count", 1), kind, get(a, "x_min"), get(a, "x_max"), get(a, "min_rel", 0.1));
      const tpl = get<any>(a, "text", "{x:.0f}");
      for (const [xp, yp] of peaks) {
        out.push({ kind: "peak", name, axis: ax, x: clean(xp), y: clean(yp), text: fmt(tpl, xp, yp, "x"),
          color: hex(col), text_color: hex(tcol), size: fs, down: kind !== "max" });
      }
      results.push({ name, sheet, peaks: peaks.map(([xp, yp]) => ({ x: pyRound(xp, 3), y: pyRound(yp, 5), text: fmt(tpl, xp, yp, "x") })) });
    } else if (t === "vline" || t === "hline") {
      const pos = (t === "vline" ? a.x : a.y) as number;
      if (stack === 0) {
        const txt = get<any>(a, "text");
        out.push({ kind: t, name, axis: ax, value: clean(pos), color: hex(or(get(a, "color"), "gray")),
          linestyle: get(a, "linestyle", "dashed"),
          text: truthy(txt) && t === "vline" ? fmt(txt, pos, null, "x") : (truthy(txt) ? fmt(txt, null, pos, "y") : ""),
          text_color: hex(or(get(a, "color"), textAll ? tc : "gray")), size: fs });
      }
      results.push({ name, sheet, [t === "vline" ? "x" : "y"]: pos });
    } else if (t === "band") {
      if (stack === 0) {
        const c = or(get(a, "color"), "gray");
        out.push({ kind: "band", name, x_min: clean(a.x_min), x_max: clean(a.x_max), fill: rgba(c, get(a, "alpha", 0.15) as number),
          text: or(get(a, "text"), "") as string, text_color: hex(or(get(a, "color"), textAll ? tc : "gray")), size: fs });
      }
      results.push({ name, sheet, x_min: a.x_min, x_max: a.x_max });
    } else if (t === "text" && get(a, "x") !== null && get(a, "y") !== null) {
      out.push({ kind: "text_at", name, axis: ax, x: clean(a.x), y: clean(a.y), text: get(a, "text", ""),
        color: hex(or(get(a, "color"), tc)), size: fs });
      results.push({ name, sheet, text: get(a, "text", ""), x: a.x, y: a.y });
    } else if (t === "text") {
      if (stack === 0) {
        out.push({ kind: "text", name, where: get(a, "where", "upper right"), text: get(a, "text", ""),
          color: hex(or(get(a, "color"), tc)), size: fs });
      }
      results.push({ name, sheet, text: get(a, "text", "") });
    }
  }
  return out;
}

/** plotkit.echarts.resolve: normalized spec + jobs -> one resolved figure per sheet (or one for all when combined),
 *  with what its labels report. */
export function resolve(spec: CurveSpec, jobs: Job[]): Resolved[] {
  const tc = spec.text_color;
  const textAll = spec._text_color_set;
  const combine = truthy(spec.combine);
  const groups = combine ? [jobs] : jobs.map(j => [j]);
  const figs: Resolved[] = [];
  for (const group of groups) {
    const first = group[0];
    const title = figureTitle(spec, first);
    const texts: unknown[] = [title, ...(["x", "y1", "y2"] as const).map(r => or(get(spec[r], "label"), "")),
      ...group.map(j => j.sheet), ...group.flatMap(j => Object.values(j.cols).map(c => c.name)),
      ...Object.values(spec.annotate).map(a => or(get(a, "text"), "")),
      JSON.stringify(or(spec.echarts, {})), ...((or(get(spec, "names"), []) as unknown[]).map(pyStrValue)),
      ...group.flatMap(j => Object.values(get<Record<string, AnnotSpec>>(j, "marks", {})).map(a => pyStrValue(or(get(a, "text"), ""))))];
    const family = fontFamily(spec, texts);
    const hasY2 = group.every(j => Object.hasOwn(j.data, "y2"));
    const series: FigureSeries[] = [], legendNames: string[] = [];
    let legendExtra: Figure["legend"]["extra"] = [];
    const split = truthy(get(spec, "panels")) && group.every(j => Object.hasOwn(j.data, "y2"));
    const points = (xs: ArrayLike<number>, ys: ArrayLike<number>): [number, number][] => {
      const n = Math.min(xs.length, ys.length), out: [number, number][] = new Array(n);
      for (let i = 0; i < n; i++) out[i] = [clean(xs[i]), clean(ys[i])];
      return out;
    };
    group.forEach((j, k) => {
      const [c1, c2, lab1] = seriesStyle(spec, j, k);
      j.colors = { y1: c1, y2: c2 };
      series.push({ axis: "y1", name: lab1, sheet: j.sheet, color: hex(c1), width: get(spec.y1, "width", 1.5),
        linestyle: get(spec.y1, "linestyle", "solid"), style: get(spec.y1, "style", "line"), points: points(j.data.x, j.data.y1) });
      legendNames.push(lab1);
    });
    if (hasY2) {
      for (const j of group) {
        const lab2 = combine ? null : or(get(spec.y2, "legend"), labels(spec, "y2", j.cols.y2));
        series.push({ axis: "y2", name: or(lab2, `${j.sheet} (y2)`) as string, sheet: j.sheet, color: hex(j.colors!.y2),
          width: get(spec.y2, "width", 1.5),
          linestyle: combine && !split ? "dashed" : get(spec.y2, "linestyle", "solid"),
          style: get(spec.y2, "style", "line"), points: points(j.data.x, j.data.y2) });
        if (truthy(lab2)) legendNames.push(lab2 as string);
      }
    }
    if (combine && hasY2 && !split) {
      legendExtra = [{ name: labels(spec, "y1", first.cols.y1), color: "#808080", linestyle: "solid" },
        { name: labels(spec, "y2", first.cols.y2), color: "#808080", linestyle: "dashed" }];
    }

    const axis = (role: "x" | "y1" | "y2", values: ArrayLike<number>[], pads: [number, number], tight = false): FigureAxis => {
      const a = spec[role];
      const lineC = combine || role === "x" ? null : get<string | null>(a, "color");
      const textC = textAll ? tc : or(lineC, tc);
      const [lo, hi, tks] = axisRange(a, nanMin(values), nanMax(values), pads[0], pads[1], tight);
      return {
        label: labels(spec, role, first.cols[role]),
        label_size: or(get(a, "label_size"), spec.font_size) as number,
        label_color: hex(or(get(a, "label_color"), textC)),
        tick_size: or(get(a, "tick_size"), spec.font_size) as number,
        tick_color: hex(or(get(a, "tick_color"), textC)),
        tick_mark_color: hex(or(or(get(a, "tick_color"), lineC), tc)),
        line_color: truthy(lineC) ? hex(lineC) : null,
        min: lo, max: hi, ticks: tks, log: truthy(get(a, "log")),
        inverse: truthy(get(a, "invert")), minor: truthy(get(a, "minor")),
      };
    };
    const axes: Figure["axes"] = {
      x: axis("x", group.map(j => j.data.x), [0, 0], true),
      y1: axis("y1", group.map(j => j.data.y1), [0.08, 0.12]),
      y2: null,
    };
    axes.y2 = hasY2 ? axis("y2", group.map(j => j.data.y2), [0.12, 0.18]) : null;
    if (!hasY2) axes.y1.line_color = null;       // a single y axis keeps a black frame, as in matplotlib

    const annResults: AnnotationResult[] = [], anns: FigureAnnotation[] = [];
    const axesOn = ["y1", ...(hasY2 ? ["y2"] : [])];
    group.forEach((j, k) => {
      anns.push(...annotations(spec, axesOn, j, j.colors!, annResults, k, combine ? j.colors!.y1 : null, textAll));
    });
    const lg = spec.legend;
    figs.push({
      group,
      figure: {
        size_in: (spec.size as unknown[]).map(pyFloat), dpi: pyFloat(spec.dpi),
        font_family: family, font_size: pyFloat(spec.font_size), text_color: hex(tc),
        title: { text: title, size: or(get(spec.title, "size"), spec.font_size * 1.2) as number,
          color: hex(or(get(spec.title, "color"), tc)) },
        tick_direction: spec.tick_direction, grid: truthy(spec.grid),
        axes, series,
        series_index: combine ? "y1 per sheet, then y2 per sheet" : "0 = y1, 1 = y2",
        legend: { show: truthy(lg.show), where: lg.where, size: or(lg.size, spec.font_size * SMALL) as number,
          names: legendNames, extra: legendExtra, color: hex(tc) },
        annotations: anns, box_peaks: combine, panels: split ? "split" : null,
        echarts: spec.echarts,
      },
      annotations: annResults,
    });
  }
  return figs;
}

/** "code" is the matplotlib engine's Python hatch: refused on ECharts, before any data is read (plotkit.echarts). */
export function checkCurveCode(spec: { code?: unknown; [k: string]: unknown }): void {
  if (truthy(get(spec, "code"))) {
    throw new PlotkitError('"code" (Python) does not work with the ECharts engine',
      'use a key (e.g. annotate band for shading), or put ECharts settings in "echarts"');
  }
}

/** What builds the jobs and their warnings, e.g. () => buildJobs(spec, files, hook) (jobs.ts): given one instead of
 *  built jobs, liveResult / renderCurves refuse "code" before it runs, in Python's order. */
export type JobsBuilder = () => Promise<[object[], string[]]> | [object[], string[]];

export interface LiveCurveResult {
  ok: true; kind: "curve"; engine: "echarts"; options: Dict[]; saved: string[]; warnings: string[]; not_done: string[];
  values: Record<string, Record<string, unknown>>;
}

/** The shared result of a live curve chart (plotkit.echarts.live_result after normalize_spec): "code" refused, the
 *  jobs (built, or a builder run after that check), then {ok, kind, engine, options (one live ECharts option per
 *  figure, plain JSON), saved: [], warnings, not_done, values}. */
export function liveResult(spec: CurveSpec, jobs: Job[], warnings?: string[]): LiveCurveResult;
export function liveResult(spec: CurveSpec, build: JobsBuilder): Promise<LiveCurveResult>;
export function liveResult(spec: CurveSpec, jobs: Job[] | JobsBuilder, warnings: string[] = []): LiveCurveResult | Promise<LiveCurveResult> {
  if (typeof jobs === "function") {
    const build = jobs;
    return (async () => {
      checkCurveCode(spec);
      const [built, w] = await build();
      return liveFrom(spec, built as Job[], w);
    })();
  }
  checkCurveCode(spec);
  return liveFrom(spec, jobs, warnings);
}

function liveFrom(spec: CurveSpec, jobs: Job[], warnings: string[]): LiveCurveResult {
  const figs = resolve(spec, jobs);
  return { ok: true, kind: "curve", engine: "echarts", options: liveOptions(figs.map(f => f.figure)), saved: [],
    warnings, not_done: notDone(spec), values: curveValues(figs.map(f => ({ annotations: f.annotations }))) };
}
