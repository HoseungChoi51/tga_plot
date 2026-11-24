// The chart spec check (port of plotkit/charts.py: is_chart_spec, _alias_top, _as_axis, normalize, _legend_where).
// A spec with a "chart" key (or type, kind, plot, 그래프 ...) is a chart; everything else is a curve (spec.ts).
import { PlotkitError } from "./errors.ts";
import {
  CHART_AGGS, CHART_AGG_ALIASES, CHART_AXIS_EXTRA_ALIASES, CHART_AXIS_KEYS, CHART_KEYS, CHART_KIND_ALIASES, CHART_KINDS,
  CHART_TOP_ALIASES, CHART_TOP_KEYS, AXIS_ALIASES, FORMATS, KOREAN_PLACES, LEGEND_PLACES,
} from "./tables.ts";
import {
  type Dict, color, expandFiles, get, isDict, isPyInt, put, pyFloat, pyInt, pyList, pyReprValue, pyStrValue, pyStrip,
  suggest, truthy,
} from "./spec.ts";

const KEYS: readonly string[] = CHART_KEYS;
const TOP_KEYS: readonly string[] = CHART_TOP_KEYS;
const AXIS_KEYS: readonly string[] = CHART_AXIS_KEYS;
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
  for (const [k, v] of Object.entries(user)) {
    const kk: string = get(CHART_TOP_ALIASES, k, get(CHART_TOP_ALIASES, k.toLowerCase(), k));
    if (kk === "output.format") {
      if (!Object.hasOwn(out, "output")) out.output = {};
      if (!isDict(out.output)) {                   // Python: TypeError (item assignment on a non-dict)
        throw new PlotkitError(`"output" must be an object when "${k}" is also given`, 'e.g. "output": {"format": "png"}');
      }
      out.output.format = v;
      continue;
    }
    put(out, kk, v);
  }
  return out;
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
      throw new PlotkitError(`unknown key "${where}.${k}".${suggest(kk, AXIS_KEYS)}`,
        `allowed keys for ${where}: ${AXIS_KEYS.join(", ")}`);
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
  const agg = get(s.y, "agg", null);
  if (agg !== null && agg !== undefined) {
    const al = pyStrValue(agg).toLowerCase();
    const a = get(CHART_AGG_ALIASES, al, al);
    if (!AGGS.includes(a)) throw new PlotkitError(`unknown y.agg "${pyStrValue(agg)}"`, "use one of: " + AGGS.join(", "));
    s.y.agg = a;
  }
  if (typeof s.y.col === "string" && Object.hasOwn(s.y, "col") && COUNT_WORDS.includes(pyStrip(s.y.col).toLowerCase())) {
    s.y = { ...s.y, col: null, agg: "count" };
  }
  if (truthy(get(s.z, "agg", null))) {
    const zl = pyStrValue(s.z.agg).toLowerCase();
    s.z.agg = get(CHART_AGG_ALIASES, zl, zl);
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
    if (lg === false || (typeof lg === "string" && ["none", "off", "없음", "숨김"].includes(lg.toLowerCase()))) {
      s.legend = { where: "best", show: false, size: null, title: null };
    } else {
      s.legend = { where: typeof lg === "string" ? lg : "best", show: true, size: null, title: null };
    }
  } else {
    if (!isDict(lg)) {                             // Python: AttributeError (.get on a list or number)
      throw new PlotkitError('"legend" must be a position text, false, or {"where": ..., "show": ..., "size": ...}');
    }
    s.legend = {
      where: get(lg, "where", get(lg, "position", get(lg, "loc", "best"))), show: get(lg, "show", true),
      size: get(lg, "size", null), title: get(lg, "title", null),
    };
  }
  s.legend.where = legendWhere(s.legend.where);
  const size0 = truthy(get(s, "size", null)) ? s.size : [6.4, 4.6];
  const size = pyList(size0)?.map(pyFloat);
  if (size === undefined || size.some(v => v === undefined)) {    // Python: ValueError / TypeError from float()
    throw new PlotkitError(`"size" must be [width, height] in inches, got ${pyReprValue(size0)}`, "e.g. [6.4, 4.6]");
  }
  s.size = size;
  const dpi0 = truthy(get(s, "dpi", null)) ? s.dpi : 300;
  const dpi = pyInt(dpi0);
  if (dpi === undefined) throw new PlotkitError(`"dpi" must be a whole number, got ${pyReprValue(dpi0)}`, "e.g. 300");
  s.dpi = dpi;
  const fs0 = truthy(get(s, "font_size", null)) ? s.font_size : 11;
  const fs = pyFloat(fs0);
  if (fs === undefined) throw new PlotkitError(`"font_size" must be a number, got ${pyReprValue(fs0)}`, "e.g. 11");
  s.font_size = fs;
  if (!Object.hasOwn(s, "font")) s.font = null;
  s._text_color_set = Object.hasOwn(s, "text_color");
  s.text_color = color(truthy(get(s, "text_color", null)) ? s.text_color : "black", "text_color");
  let out: unknown = truthy(get(s, "output", null)) ? s.output : {};
  if (typeof out === "string") out = { format: out };
  if (!isDict(out)) {                              // Python: AttributeError (.get on a list or number)
    throw new PlotkitError(`"output" must be an object, got ${pyReprValue(out)}`, 'e.g. "output": {"format": "png"}');
  }
  const fmt0 = get(out, "format", "png");
  const fmt = (Array.isArray(fmt0) ? fmt0 : [fmt0])
    .map(x => pyStrValue(x).toLowerCase().replace(/^\.+/, "").replaceAll("jpeg", "jpg").replaceAll("tiff", "tif"));
  for (const x of fmt) {
    if (!FORMAT_LIST.includes(x)) throw new PlotkitError(`unknown output format "${x}"`, "use png, pdf, svg, jpg or tif");
  }
  s.output = { dir: get(out, "dir", null), format: fmt, name: get(out, "name", null) };
  s.asks = truthy(get(s, "asks", null)) ? s.asks : [];
  return s;
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
