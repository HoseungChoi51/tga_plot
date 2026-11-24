// The spec check (curves: spec.ts, charts: chartspec.ts, "echarts" patches: patch.ts) against Python's normalize on
// every reference and model-written spec of the golden corpus.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { join } from "node:path";
import { golden, diff, BASES } from "./golden.ts";
import { normalizeSpec, notDone, expandFiles } from "../src/spec.ts";
import { normalizeChart, isChartSpec } from "../src/chartspec.ts";
import { validatePatch } from "../src/patch.ts";
import { PlotkitError } from "../src/errors.ts";

const CASES = golden("specs");

/** Cases that cannot match, with the reason (none so far). */
const EXPECTED_DIFFS: Record<string, string> = {};

function listNames(dir: string, prefix = ""): string[] {
  const out: string[] = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) out.push(...listNames(join(dir, e.name), `${prefix}${e.name}/`));
    else if (e.isFile()) out.push(prefix + e.name);
  }
  return out;
}

const NAMES = new Map<string, string[]>();
function names(base: string): string[] {
  if (!NAMES.has(base)) NAMES.set(base, listNames(BASES[base]));
  return NAMES.get(base)!;
}

type Outcome = { ok: any } | { error: string; hint: string } | { crash: string };

function run(c: any): Outcome {
  try {
    const norm = c.kind === "chart" ? normalizeChart(c.spec, names(c.base)) : normalizeSpec(c.spec, names(c.base));
    return { ok: norm };
  } catch (e) {
    if (e instanceof PlotkitError) return { error: e.message, hint: e.hint };
    return { crash: String((e as Error)?.stack ?? e) };
  }
}

function check(c: any): string | null {
  const got = run(c);
  if ("crash" in got) return `${c.id}: crashed: ${got.crash.slice(0, 300)}`;
  if ("normalized_full" in c) {
    if (!("ok" in got)) return `${c.id}: error ${JSON.stringify(got)}, want a normalized spec`;
    const d = diff(got.ok, c.normalized_full);
    return d.length ? `${c.id}: ${d.slice(0, 5).join("; ")}` : null;
  }
  if ("normalize_error" in c) {
    if (!("error" in got)) return `${c.id}: normalized, want error ${JSON.stringify(c.normalize_error)}`;
    const want = c.normalize_error;
    return got.error === want.error && got.hint === want.hint ? null
      : `${c.id}: ${JSON.stringify([got.error, got.hint])} != ${JSON.stringify([want.error, want.hint])}`;
  }
  if ("normalize_crash" in c) {                     // a Python bug: the port answers with a PlotkitError
    return "error" in got && got.error ? null : `${c.id}: Python crashed (${c.normalize_crash}); want a PlotkitError, got ${JSON.stringify(got).slice(0, 200)}`;
  }
  return `${c.id}: case has no expected outcome`;
}

function failures(kind: string, field: string): string[] {
  const out: string[] = [];
  for (const c of CASES) {
    if (c.kind !== kind || !(field in c)) continue;
    const m = check(c);
    if (m && !(c.id in EXPECTED_DIFFS)) out.push(m);
    if (!m && c.id in EXPECTED_DIFFS) out.push(`${c.id}: listed as an expected difference but matches now`);
    if (out.length > 15) break;
  }
  return out;
}

test("the corpus has the cases the port is checked on", () => {
  assert.equal(CASES.length, 3832);
  assert.ok(CASES.every(c => (c.kind === "chart") === isChartSpec(c.spec)));
});

test("curve specs normalize as in Python", () => assert.deepEqual(failures("curve", "normalized_full"), []));
test("chart specs normalize as in Python", () => assert.deepEqual(failures("chart", "normalized_full"), []));
test("curve spec errors and hints equal Python's", () => assert.deepEqual(failures("curve", "normalize_error"), []));
test("chart spec errors and hints equal Python's", () => assert.deepEqual(failures("chart", "normalize_error"), []));
test("specs that crash Python give a PlotkitError", () => {
  assert.deepEqual([...failures("curve", "normalize_crash"), ...failures("chart", "normalize_crash")], []);
});

// ------------------------------------------------------------------- hand-written cases
// [case, Python 3.13's outcome] (ok / error and hint / crash: a Python exception, where the port gives a PlotkitError).
// They cover what the corpus has little of: Python's str()/repr() in messages, float() of text, aliases, glob.
const HAND: [any, any][] = [
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "y1": {"normalize": 1}}}, {"error": "unknown key \"y1.normalize\".", "hint": "allowed keys for y1: col, color, flip, invert, label, label_color, label_size, legend, linestyle, log, max, min, minor, show, step, style, tick_color, tick_size, width"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "xmin": 3}}, {"error": "\"xmin\" belongs to an axis, not the top level", "hint": "put it inside \"x\", \"y1\" or \"y2\", e.g. \"x\": {\"min\": ...}"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "residue": 3}}, {"error": "\"residue\" belongs inside \"annotate\"", "hint": "e.g. \"annotate\": {\"residue\": {\"x\": 700}} or \"annotate\": {\"vline1\": {\"type\": \"vline\", \"x\": 450}}"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "titel": "x"}}, {"error": "unknown key \"titel\". Did you mean \"title\"?", "hint": "top-level keys: file, sheets, preset, read, x, y1, y2, annotate, title, legend, text_color, tick_direction, code, echarts, grid, size, dpi, font, font_size, combine, colors, names, offset, panels, data_code, asks, output"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "x": {"step": "1e"}}}, {"error": "x.step must be a number, got '1e'", "hint": "write a plain number, e.g. 200"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "y1": {"color": "it's"}}}, {"error": "y1.color: \"it's\" is not a color", "hint": "use a name like \"red\", \"navy\", \"black\" or a hex code like \"#c0392b\""}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "annotate": {"foo": {"x": 3}}}}, {"error": "annotate.foo needs a \"type\"", "hint": "types: band, hline, peak, text, value_at_x, vline"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "annotate": {"peak": {"type": "peek"}}}}, {"error": "annotate.peak.type 'peek' unknown. Did you mean \"peak\"?", "hint": "types: band, hline, peak, text, value_at_x, vline"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "legend": {"where": "upper middle"}}}, {"error": "legend position 'upper middle' unknown", "hint": "use one of: best, upper right, upper left, lower left, lower right, right, center left, center right, lower center, upper center, center, none, outside right, outside bottom"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "format": "gif"}}, {"error": "output.format 'gif' not supported", "hint": "use png, pdf, svg, jpg or tif"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "*.xlsx"}}, {"error": "no file matches *.xlsx", "hint": "check the folder and the pattern"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "x": [1, {"a": null, "b": true}]}}, {"error": "\"x\" must be an object like {\"col\": \"B\"}, got [1, {'a': None, 'b': True}]", "hint": ""}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "annotate": {"band1": {"x_min": "１２", "x_max": "1_000", "alpha": " 0,5 "}}}}, {"ok": {"file": ["a.csv"], "sheets": "all", "preset": "tga", "read": {"header_row": null, "data_start_row": null, "sep": null, "decimal": null, "encoding": null}, "x": {"col": null, "label": "Temperature (°C)", "min": null, "max": null, "step": null, "log": false, "label_size": null, "label_color": null, "tick_size": null, "tick_color": null, "minor": false, "invert": false, "_preset_label": true}, "y1": {"col": null, "label": "Weight (%)", "min": null, "max": null, "step": null, "color": "#1f4e9c", "width": 1.8, "linestyle": "solid", "style": "line", "flip": "none", "log": false, "legend": null, "show": true, "label_size": null, "label_color": null, "tick_size": null, "tick_color": null, "minor": false, "invert": false, "_preset_label": true}, "y2": {"col": null, "label": "Deriv. weight (%/°C)", "min": null, "max": null, "step": null, "color": "#c0392b", "width": 1.4, "linestyle": "solid", "style": "line", "flip": "peaks_up", "log": false, "legend": null, "show": true, "label_size": null, "label_color": null, "tick_size": null, "tick_color": null, "minor": false, "invert": false, "_preset_label": true}, "annotate": {"residue": {"type": "value_at_x", "on": "y1", "x": 800, "method": "nearest", "text": "Residue {y:.1f}%", "_preset_text": true}, "peak": {"type": "peak", "on": "y2", "count": 1, "x_min": 150, "text": "{x:.0f} °C", "_preset_text": true}, "band1": {"x_min": 12.0, "x_max": 1000.0, "alpha": 0.5, "_requested": true, "type": "band"}}, "title": {"text": "{sheet}", "size": null, "color": null}, "legend": {"where": "center left", "show": true, "size": null}, "text_color": "black", "tick_direction": "in", "code": null, "echarts": null, "grid": false, "size": [6.4, 4.6], "dpi": 300, "font": null, "font_size": 11, "combine": false, "colors": null, "names": null, "offset": null, "panels": null, "data_code": null, "asks": [], "output": {"dir": null, "format": ["png"], "name": null}, "_text_color_set": false}}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "annotate": {"residue": {"x": "800°C"}}}}, {"error": "annotate.residue.x must be a number, got '800°C'", "hint": "write a plain number, e.g. 200"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "y2": {"flip": [1]}}}, {"crash": "TypeError: unhashable type: 'list'"}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "x": "B", "x.min": 0}}, {"crash": "TypeError: 'str' object does not support item assignment"}],
  [{"kind": "curve", "names": ["a.csv", "data/b.csv"], "spec": {"File": "a.csv", "y": {"colour": "빨강", "lw": "2,5", "range": [0, "100"], "sign": "up", "visible": 0}, "y2": false, "x": {"flip": "no", "minor_ticks": "yes", "tick_color": "c0392b"}, "annotate": [{"type": "vline", "x": "450", "linestyle": "점선"}, {"type": "text", "text": "hi", "where": "upper left", "on": 2}], "legend": "오른쪽 위", "ticks": "바깥쪽", "panels": 2, "data_code": ["a", "b"], "format": ["JPEG", ".tiff"], "colors": {"s1": "navy", "s2": "0.5"}, "names": "one", "offset": "20", "echarts": {"xaxis": {"min": 0}, "series": {"z": 3}}, "title": {"label": "T", "fontsize": 14, "colour": "검정"}, "text_colour": "회색", "output_dir": "out", "files": ["data/*.csv", "a.csv"], "preset": "TGA", "asks": {"ask": "x", "how": "no"}}}, {"ok": {"file": ["data/b.csv", "a.csv"], "sheets": "all", "preset": "tga", "read": {"header_row": null, "data_start_row": null, "sep": null, "decimal": null, "encoding": null}, "x": {"col": null, "label": "Temperature (°C)", "min": null, "max": null, "step": null, "log": false, "label_size": null, "label_color": null, "tick_size": null, "tick_color": "#c0392b", "minor": true, "invert": false, "_preset_label": true}, "y1": {"col": null, "label": "Weight (%)", "min": 0.0, "max": 100.0, "step": null, "color": "red", "width": 2.5, "linestyle": "solid", "style": "line", "flip": "peaks_up", "log": false, "legend": null, "show": 0, "label_size": null, "label_color": null, "tick_size": null, "tick_color": null, "minor": false, "invert": false, "_preset_label": true}, "y2": {"col": null, "label": "Deriv. weight (%/°C)", "min": null, "max": null, "step": null, "color": "#c0392b", "width": 1.4, "linestyle": "solid", "style": "line", "flip": "peaks_up", "log": false, "legend": null, "show": false, "label_size": null, "label_color": null, "tick_size": null, "tick_color": null, "minor": false, "invert": false, "_preset_label": true}, "annotate": {"vline_1": {"type": "vline", "x": 450.0, "linestyle": "dotted", "_requested": true}, "text_2": {"type": "text", "text": "hi", "where": "upper left", "on": "y2", "_requested": true}}, "title": {"text": "T", "size": 14, "color": "black"}, "legend": {"where": "upper right", "show": true, "size": null}, "text_color": "gray", "tick_direction": "out", "code": null, "echarts": {"xAxis": {"min": 0}, "series": [{"z": 3}]}, "grid": false, "size": [6.4, 4.6], "dpi": 300, "font": null, "font_size": 11, "combine": false, "colors": ["navy", "0.5"], "names": ["one"], "offset": 20.0, "panels": "split", "data_code": "a\nb", "asks": [{"ask": "x", "how": "no"}], "output": {"dir": "out", "format": ["jpg", "tif"], "name": null}, "_text_color_set": true}}],
  [{"kind": "curve", "names": ["a.csv"], "spec": {"file": "a.csv", "preset": null, "annotate": {"residue": true, "peak": false, "vline1": {"x": 3}}}}, {"error": "annotate.residue needs \"x\"", "hint": "e.g. \"annotate\": {\"residue\": {\"x\": 800}}"}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"file": "a.csv", "chart": "bars3"}}, {"error": "unknown chart \"bars3\"", "hint": "use one of: bar, hbar, line, scatter, histogram, heatmap, pie"}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"file": "a.csv", "chart": "bar", "x": {"colour": 1}}}, {"error": "unknown key \"x.colour\". Did you mean \"col\"?", "hint": "allowed keys for x: _names, agg, bins, col, date_format, flip, format, label, label_size, log, max, min, order, period, rotate, step, tick_size"}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"file": "a.csv", "chart": "bar", "y": {"col": "a", "agg": "avrg"}}}, {"error": "unknown y.agg \"avrg\"", "hint": "use one of: mean, sum, count, median, min, max, std, first, last, nunique"}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"file": "a.csv", "chart": "bar", "legend": "middle"}}, {"error": "unknown legend position \"middle\"", "hint": "use best, upper right, upper left, lower left, lower right, right, center left, center right, lower center, upper center, center, none, outside right, outside bottom, \"outside right\" or \"outside bottom\""}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"files": "a.csv", "type": "막대", "orient": "h", "y": [{"col": "a", "label": "A"}, "b"], "by": {"column": "k", "order": ["x"]}, "legend": {"position": "그래프 밖 아래"}, "size": ["7", 3], "dpi": "150", "format": "SVG", "z": {"col": " 개수 ", "agg": "AVG"}, "filter": "a == 1", "title": "T"}}, {"ok": {"file": ["a.csv"], "chart": "hbar", "orient": "h", "y": {"col": ["a", "b"], "_names": {"a": "A"}}, "by": "k", "legend": {"where": "outside bottom", "show": true, "size": null, "title": null}, "size": [7.0, 3.0], "dpi": 150, "output": {"dir": null, "format": ["svg"], "name": null}, "z": {"col": null, "agg": "count"}, "filter": ["a == 1"], "title": {"text": "T", "size": null, "color": null}, "sheets": null, "read": {}, "x": {}, "_by_order": ["x"], "font_size": 11.0, "font": null, "_text_color_set": false, "text_color": "black", "asks": []}}],
  [{"kind": "chart", "names": ["a.csv"], "spec": {"file": "a.csv", "chart": "bar", "size": "6x4"}}, {"crash": "ValueError: could not convert string to float: 'x'"}],
  [{"kind": "patch", "spec": {"series": [{"linestyle": {"type": "dotted"}}]}}, {"error": "unknown path \"echarts.series[0].linestyle\"", "hint": "did you mean series[0].lineStyle? allowed here: name, lineStyle, itemStyle, areaStyle, symbol, symbolSize, showSymbol, smooth, step, z, label, emphasis, markArea, markLine, markPoint"}],
  [{"kind": "patch", "spec": {"title": {"text": "javascrİpt:alert(1)"}}}, {"error": "echarts.title.text: links, data URLs and code are not allowed", "hint": "write plain text, numbers or colours only"}],
  [{"kind": "patch", "spec": {"graphic": {"type": "image"}}}, {"error": "echarts.graphic[0].type must be one of text, line, rect", "hint": ""}],
  [{"kind": "patch", "spec": {"series": [{"markLine": {"data": [[{"xAxis": 1}, {"xAxis": 2}, {}]]}}]}}, {"error": "echarts.series[0].markLine.data[0] must be one item or a [start, end] pair", "hint": ""}],
  [{"kind": "patch", "spec": "{\"xaxis\": {\"min\": 0}, \"series\": {\"z\": 3}}"}, {"ok": {"xAxis": {"min": 0}, "series": [{"z": 3}]}}],
  [{"kind": "not_done", "spec": {"asks": [{"ask": "3D", "how": "Unsupported"}, {"ask": "x", "how": "key"}, "loose", {"how": "no"}]}}, {"ok": ["3D", ""]}],
  [{"kind": "not_done", "spec": {"asks": null}}, {"ok": []}],
  [{"kind": "expand", "names": ["data/raman/R2.csv", "data/raman/R1.csv", "data/raman/.hidden.csv", "data/b.xlsx", "a.csv", "data/raman/sub/x.csv"], "spec": ["data/raman/*.csv", "data/*", "*/*/R[!2].csv", "a.csv", "./data/raman/R?.csv", "data/raman/.*", "d*/"]}, {"ok": ["data/raman/R1.csv", "data/raman/R2.csv", "data/b.xlsx", "data/raman", "data/raman/R1.csv", "a.csv", "./data/raman/R1.csv", "./data/raman/R2.csv", "data/raman/.hidden.csv", "data/"]}],
];

function runHand(c: any): any {
  switch (c.kind) {
    case "curve": return normalizeSpec(c.spec, c.names);
    case "chart": return normalizeChart(c.spec, c.names);
    case "patch": return validatePatch(c.spec);
    case "not_done": return notDone(c.spec);
    case "expand": return expandFiles(c.spec, c.names);
  }
  throw new Error(c.kind);
}

test("hand-written cases give Python's results", () => {
  const bad: string[] = [];
  for (const [c, want] of HAND) {
    let got: any;
    try {
      got = { ok: runHand(c) };
    } catch (e) {
      if (!(e instanceof PlotkitError)) throw e;
      got = { error: e.message, hint: e.hint };
    }
    const tag = JSON.stringify(c.spec).slice(0, 80);
    if ("ok" in want) {
      const d = "ok" in got ? diff(got.ok, want.ok) : [JSON.stringify(got)];
      if (d.length) bad.push(`${tag}: ${d.join("; ")}`);
    } else if ("error" in want) {
      if (got.error !== want.error || got.hint !== want.hint) bad.push(`${tag}: ${JSON.stringify(got)} != ${JSON.stringify(want)}`);
    } else if (!("error" in got)) {
      bad.push(`${tag}: Python crashed (${want.crash}); want a PlotkitError, got ${JSON.stringify(got).slice(0, 120)}`);
    }
  }
  assert.deepEqual(bad, []);
});

test("an echarts patch over 4096 bytes is refused", () => {
  assert.throws(() => validatePatch({ title: { text: "x".repeat(4100) } }),
    { message: '"echarts" is larger than 4096 bytes', hint: "keep it to the few settings no key covers" } as any);
});

test("a JS spec is not changed by normalizing it (Python may change the caller's dicts)", () => {
  const spec = { file: "a.csv", output: { dir: "x" }, outdir: "y", y: { col: "C" }, y1: { color: "red" } };
  const copy = structuredClone(spec);
  const s = normalizeSpec(spec, ["a.csv"]);
  assert.deepEqual(spec, copy);
  assert.deepEqual([s.output.dir, s.y1.col, s.y1.color], ["y", "C", "red"]);
});
