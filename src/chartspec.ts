// The chart spec check (port of plotkit/charts.py: is_chart_spec, _alias_top, _as_axis, normalize, _legend_where).
// A spec with a "chart" key (or type, kind, plot, 그래프 ...) is a chart; everything else is a curve (spec.ts).
import { PlotkitError } from "./errors.ts";
import {
  CHART_AGGS, CHART_AGG_ALIASES, CHART_AXIS_EXTRA_ALIASES, CHART_AXIS_KEYS, CHART_KEYS, CHART_KIND_ALIASES, CHART_KINDS,
  CHART_TOP_ALIASES, CHART_TOP_KEYS, AXIS_ALIASES, FORMATS, KOREAN_PLACES, LEGEND_PLACES,
} from "./tables.ts";
import {
  type Dict, color, expandFiles, get, givenTwice, isDict, isPyInt, put, pyFloat, pyReprValue, pyStrValue, pyStrip,
  suggest, truthy,
} from "./spec.ts";

const KEYS: readonly string[] = CHART_KEYS;
const TOP_KEYS: readonly string[] = CHART_TOP_KEYS;
const AXIS_KEYS: readonly string[] = CHART_AXIS_KEYS;
const PUBLIC_AXIS_KEYS = AXIS_KEYS.filter(k => !k.startsWith("_"));          // not the internal _names
const KINDS: readonly string[] = CHART_KINDS;
const AGGS: readonly string[] = CHART_AGGS;
const PLACES: readonly string[] = LEGEND_PLACES;
const FORMAT_LIST: readonly string[] = FORMATS;
const COUNT_WORDS = ["count", "개수", "건수", "n"];

/** True when the spec names a chart under "chart" or any of its aliases (the router sends it here). */
export function isChartSpec(user: unknown): boolean {
  return isDict(user) && Object.keys(user).some(k => KEYS.includes(k) || KEYS.includes(k.toLowerCase()));
}

function aliasTop(user: Dict): Dict {
  const out: Dict = {};
  let fmt: [string, unknown] | null = null;
  for (const [k, v] of Object.entries(user)) {
    const kk: string = get(CHART_TOP_ALIASES, k, get(CHART_TOP_ALIASES, k.toLowerCase(), k));
    if (kk === "output.format") {
      fmt = [k, v];
      continue;
    }
    put(out, kk, v);
  }
  if (fmt !== null) {                              // "format" goes into "output", before or after it
    const [k, v] = fmt;
    if (!Object.hasOwn(out, "output")) out.output = { format: v };
    else if (isDict(out.output)) out.output.format = v;
    else throw givenTwice("output", "format", out.output, k);
  }
  return out;
}

/** _number: a finite number from a number or numeric text; null for anything else (true/false, lists, "6in"). */
function number(v: unknown): number | null {
  if (typeof v !== "number" && typeof v !== "string") return null;
  const f = pyFloat(v);
  return f !== undefined && Number.isFinite(f) ? f : null;
}

function asAxis(v: unknown, where: string): Dict {
  if (v === null || v === undefined) return {};
  if (typeof v === "string" || isPyInt(v)) return { col: v };
  if (Array.isArray(v)) {                          // several columns: names, or {"col", "label"} each
    const cols = v.map(x => (isDict(x) ? get(x, "col", get(x, "column", null)) : x));
    const names: Dict = {};
    cols.forEach((c, i) => {
      const x = v[i];
      if (isDict(x) && truthy(get(x, "label", null))) put(names, pyStrValue(c), x.label);
    });
    return { col: cols, ...(Object.keys(names).length ? { _names: names } : {}) };
  }
  if (!isDict(v)) {
    throw new PlotkitError(`"${where}" must be a column name or a dict`, 'e.g. "x": "반응기" or "x": {"col": "B", "label": "..."}');
  }
  const d: Dict = {};
  for (const [k, val] of Object.entries(v)) {
    let kk: string = get(AXIS_ALIASES, k, k);
    kk = get(CHART_AXIS_EXTRA_ALIASES, kk, kk);
    if (!AXIS_KEYS.includes(kk)) {
      throw new PlotkitError(`unknown key "${where}.${k}".${suggest(kk, PUBLIC_AXIS_KEYS)}`,
        `allowed keys for ${where}: ${PUBLIC_AXIS_KEYS.join(", ")}`);
    }
    put(d, kk, val);
  }
  return d;
}

/** Check a chart spec and fill in its defaults. names: the files the host gave, for patterns in "file". The result
 *  keeps the internal keys later stages read (_names, _by_order, _text_color_set). */
export function normalizeChart(user: unknown, names: readonly string[] = []): Dict {
  if (!isDict(user)) throw new PlotkitError("the spec must be a JSON object");
  const s = aliasTop(structuredClone(user));
  const unknown = Object.keys(s).filter(k => !TOP_KEYS.includes(k));
  if (unknown.length) {
    const k = unknown[0];
    throw new PlotkitError(`unknown key "${k}" for a chart.${suggest(k, TOP_KEYS)}`,
      "chart keys: " + TOP_KEYS.filter(x => x !== "engine" && x !== "notes").join(", "));
  }
  let kind = pyStrip(pyStrValue(get(s, "chart", ""))).toLowerCase();
  kind = get(CHART_KIND_ALIASES, kind, kind);
  if (!KINDS.includes(kind)) throw new PlotkitError(`unknown chart "${pyStrValue(get(s, "chart", null))}"`, "use one of: " + KINDS.join(", "));
  if (["h", "horizontal", "가로"].includes(pyStrValue(get(s, "orient", "")).toLowerCase()) && kind === "bar") kind = "hbar";
  s.chart = kind;
  const f = get(s, "file", null);
  if (!truthy(f)) throw new PlotkitError('missing "file"', 'add "file": "<data file>"');
  s.file = expandFiles(Array.isArray(f) ? f : [f], names);
  if (!Object.hasOwn(s, "sheets")) s.sheets = null;
  s.read = truthy(get(s, "read", null)) ? s.read : {};
  for (const role of ["x", "y", "z"]) s[role] = asAxis(get(s, role, null), role);
  const by = get(s, "by", null);
  if (isDict(by)) {
    s.by = truthy(get(by, "col", null)) ? by.col : get(by, "column", null);
    if (truthy(get(by, "order", null))) s._by_order = by.order;
    if (truthy(get(by, "colors", null))) s.colors = by.colors;
  }
  for (const role of ["y", "z"]) {
    const agg = get(s[role], "agg", null);
    if (agg !== null && agg !== undefined) {
      const al = pyStrValue(agg).toLowerCase();
      const a = get(CHART_AGG_ALIASES, al, al);
      if (!AGGS.includes(a)) throw new PlotkitError(`unknown ${role}.agg "${pyStrValue(agg)}"`, "use one of: " + AGGS.join(", "));
      s[role].agg = a;
    }
  }
  if (typeof s.y.col === "string" && Object.hasOwn(s.y, "col") && COUNT_WORDS.includes(pyStrip(s.y.col).toLowerCase())) {
    s.y = { ...s.y, col: null, agg: "count" };
  }
  if (typeof s.z.col === "string" && Object.hasOwn(s.z, "col") && COUNT_WORDS.includes(pyStrip(s.z.col).toLowerCase())) {
    s.z = { col: null, agg: "count" };
  }
  let filt: unknown = truthy(get(s, "filter", null)) ? s.filter : [];
  if (typeof filt === "string" || isDict(filt)) filt = [filt];
  s.filter = filt;
  const title = get(s, "title", null);
  if (title === null || typeof title === "string") s.title = { text: title, size: null, color: null };
  const lg = get(s, "legend", null);
  if (lg === null || typeof lg === "string" || typeof lg === "boolean") {
    if (lg === false || legendOff(lg)) {
      s.legend = { where: "best", show: false, size: null, title: null };
    } else {
      s.legend = { where: typeof lg === "string" ? lg : "best", show: true, size: null, title: null };
    }
  } else if (isDict(lg)) {
    const where = get(lg, "where", get(lg, "position", get(lg, "loc", "best")));
    s.legend = {
      where: legendOff(where) ? "best" : where, show: legendOff(where) ? false : get(lg, "show", true),
      size: get(lg, "size", null), title: get(lg, "title", null),
    };
  } else {
    throw new PlotkitError('"legend" must be a position text, false, or {"where": ..., "show": ..., "size": ...}',
      'e.g. "legend": "upper right", "legend": false or "legend": {"where": "outside right"}');
  }
  s.legend.where = legendWhere(s.legend.where);
  const size: unknown = truthy(get(s, "size", null)) ? s.size : [6.4, 4.6];
  const wh = Array.isArray(size) ? size.map(number) : [];
  if (wh.length !== 2 || wh.some(v => v === null || v <= 0)) {
    throw new PlotkitError(`"size" must be [width, height] in inches, got ${pyReprValue(size)}`, 'e.g. "size": [6.4, 4.6]');
  }
  s.size = wh;
  const dpi = number(truthy(get(s, "dpi", null)) ? s.dpi : 300);
  if (dpi === null || dpi < 1) {
    throw new PlotkitError(`"dpi" must be a number of 1 or more, got ${pyReprValue(get(s, "dpi", null))}`, 'e.g. "dpi": 300');
  }
  s.dpi = Math.trunc(dpi);
  const fs = number(truthy(get(s, "font_size", null)) ? s.font_size : 11);
  if (fs === null || fs <= 0) {
    throw new PlotkitError(`"font_size" must be a number above 0, got ${pyReprValue(get(s, "font_size", null))}`, 'e.g. "font_size": 11');
  }
  s.font_size = fs;
  if (get(s, "point_size", null) != null) {
    const ps = number(s.point_size);
    if (ps === null || ps <= 0) {
      throw new PlotkitError(`"point_size" must be a number above 0, got ${pyReprValue(s.point_size)}`,
        'e.g. "point_size": 30 (one marker size for all points; sizes from a column are not supported)');
    }
    s.point_size = ps;
  }
  if (get(s, "alpha", null) != null) {
    const al = number(s.alpha);
    if (al === null || !(0 <= al && al <= 1)) {
      throw new PlotkitError(`"alpha" must be a number from 0 to 1, got ${pyReprValue(s.alpha)}`, 'e.g. "alpha": 0.6 (1 = opaque)');
    }
    s.alpha = al;
  }
  if (!Object.hasOwn(s, "font")) s.font = null;
  s._text_color_set = Object.hasOwn(s, "text_color");
  s.text_color = color(truthy(get(s, "text_color", null)) ? s.text_color : "black", "text_color");
  let out: unknown = truthy(get(s, "output", null)) ? s.output : {};
  if (typeof out === "string") out = { format: out };
  if (!isDict(out)) throw new PlotkitError(`"output" must be an object, got ${pyReprValue(out)}`, 'e.g. "output": {"format": "png"}');
  const fmt0 = get(out, "format", "png");
  const fmt = (Array.isArray(fmt0) ? fmt0 : [fmt0])
    .map(x => pyStrValue(x).toLowerCase().replace(/^\.+/, "").replaceAll("jpeg", "jpg").replaceAll("tiff", "tif"));
  for (const x of fmt) {
    if (!FORMAT_LIST.includes(x)) throw new PlotkitError(`unknown output format "${x}"`, "use png, pdf, svg, jpg or tif");
  }
  s.output = { dir: get(out, "dir", null), format: fmt, name: get(out, "name", null) };
  const asks = truthy(get(s, "asks", null)) ? s.asks : [];
  s.asks = Array.isArray(asks) ? asks : [asks];   // one ask given without a list
  return s;
}

/** _legend_off: a legend position that means no legend ("none", "off", "없음", "숨김"). */
function legendOff(w: unknown): boolean {
  return typeof w === "string" && ["none", "off", "없음", "숨김"].includes(pyStrip(w).toLowerCase());
}

/** A legend position: Korean names, "outside ..." forms, or one of LEGEND_PLACES. */
export function legendWhere(w: unknown): string {
  let s = pyStrip(pyStrValue(truthy(w) ? w : "best")).toLowerCase();
  s = get(KOREAN_PLACES, s, s);
  if (["outside", "바깥", "밖"].some(t => s.includes(t))) {
    return ["bottom", "아래", "below", "하단"].some(t => s.includes(t)) ? "outside bottom" : "outside right";
  }
  if (!PLACES.includes(s)) {
    throw new PlotkitError(`unknown legend position "${s}"`, "use " + PLACES.join(", ") + ', "outside right" or "outside bottom"');
  }
  return s;
}
