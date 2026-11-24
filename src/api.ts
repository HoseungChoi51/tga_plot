// What an app calls: check a spec against its files, get live ECharts options, or SVG for export.
// Port of plotkit/api.py with plotkit.core.route and charts.curve_as_chart. Files come as {name, bytes}; a spec's
// file names refer to those names. data_code runs only through the host's sandbox (opts.runCode).
import { PlotkitError } from "./errors.ts";
import type { InputFile, RunCode } from "./types.ts";
import { normalizeSpec, normalizeAnnotations, expandFiles, pyStrValue, truthy } from "./spec.ts";
import { isChartSpec, normalizeChart } from "./chartspec.ts";
import { validatePatch } from "./patch.ts";
import { buildJobs } from "./jobs.ts";
import type { DataCodeHook } from "./jobs.ts";
import { findCol, loadFrame } from "./frame.ts";
import * as charts from "./charts.ts";
import * as curves from "./curves.ts";
import { renderCurves } from "./render.ts";
import type { OnChart } from "./render.ts";
import { renderChartSvg } from "./chart_render.ts";
import { runChartDataCode, runCurveDataCode } from "./hatch.ts";

export interface Options {
  /** The host's sandbox for data_code (KetchupE: its QuickJS runner). Without it, data_code is refused. */
  runCode?: RunCode;
  signal?: AbortSignal;
}

export type Kind = "curve" | "chart";
type Spec = Record<string, any>;

const CHART_CODE = ['"code" only works with the matplotlib engine',
  'use "data_code" for data changes (both engines), or an "echarts" patch for drawing changes'] as const;
const CURVE_CODE = ['"code" (Python) does not work with the ECharts engine',
  'use a key (e.g. annotate band for shading), or put ECharts settings in "echarts"'] as const;

const isObj = (v: unknown): v is Spec => !!v && typeof v === "object" && !Array.isArray(v);
const names = (files: InputFile[]) => files.map(f => f.name);

/** charts.curve_as_chart: a curve spec whose x column holds dates (a sensor log) as the same plot as a chart line;
 *  null when x is not a date column. */
export async function curveAsChart(user: Spec, files: InputFile[]): Promise<Spec | null> {
  let c: string;
  const x = user.x;
  try {
    const xcol = isObj(x) ? x.col : x;
    if (!truthy(xcol)) return null;
    const fl = expandFiles(Array.isArray(user.file) ? user.file : [user.file], names(files));
    const sheets = user.sheets === undefined || user.sheets === null || user.sheets === "all" ? null : user.sheets;
    const df = await loadFrame({ file: fl, sheets, read: truthy(user.read) ? user.read : {} } as any, files);
    c = findCol(df, xcol, "x");
    if (df.dtypes[df.columns.indexOf(c)] !== "datetime") return null;
  } catch {
    return null;
  }
  const ys: unknown[] = [];
  for (const role of ["y1", "y2"]) {
    const v = user[role];
    const col = isObj(v) ? v.col : typeof v === "string" ? v : null;
    if (truthy(col)) ys.push(col);
  }
  if (!ys.length) return null;
  const out: Spec = { file: user.file, chart: "line", x: { col: c, ...(isObj(x) && truthy(x.label) ? { label: x.label } : {}) },
    y: ys.length > 1 ? ys : ys[0] };
  for (const k of ["sheets", "read", "title", "legend", "size", "dpi", "font", "font_size", "text_color", "grid", "output", "asks", "filter"]) {
    const v = user[k];
    if (v !== undefined && v !== null && v !== "all") out[k] = v;
  }
  const cols = ["y1", "y2"].filter(r => isObj(user[r]) && truthy(user[r].color)).map(r => user[r].color);
  if (cols.length) out.colors = cols;
  if (isObj(user.y1) && truthy(user.y1.label) && ys.length === 1) out.y = { col: ys[0], label: user.y1.label };
  return out;
}

/** plotkit.core.route: where a spec goes. */
export async function route(spec: unknown, files: InputFile[]): Promise<[Kind, unknown]> {
  if (isChartSpec(spec)) return ["chart", spec];
  if (isObj(spec) && truthy(spec.file)) {
    const alt = await curveAsChart(spec, files);
    if (alt) return ["chart", alt];
  }
  return ["curve", spec];
}

/** The chart spec ready to draw (data_code applied to the table through the host's sandbox), and its table. */
async function chartInput(user: unknown, files: InputFile[], opts: Options) {
  const norm = normalizeChart(user, names(files)) as Spec;
  let frame = await loadFrame(norm as any, files);
  if (truthy(norm.data_code)) {
    const code = Array.isArray(norm.data_code) ? norm.data_code.join("\n") : String(norm.data_code);
    frame = await runChartDataCode(code, frame, opts.runCode, opts.signal);
  }
  return { norm, spec: { ...norm, data_code: null } as Spec, frame };
}

function curveHook(opts: Options): DataCodeHook {
  const mark = (name: string, m: Record<string, unknown>) => normalizeAnnotations({ [name]: m })[0][name] as Record<string, unknown>;
  return (async (spec: Spec, data: Record<string, number[]>, sheet: string) => {
    const code = Array.isArray(spec.data_code) ? spec.data_code.join("\n") : String(spec.data_code);
    return runCurveDataCode(code, data, sheet, opts.runCode, mark, opts.signal);
  }) as unknown as DataCodeHook;
}

async function curveInput(user: unknown, files: InputFile[], opts: Options) {
  const norm = normalizeSpec(user, names(files)) as Spec;
  if (truthy(norm.code)) throw new PlotkitError(...CURVE_CODE);
  const [jobs, warnings] = await buildJobs(norm as any, files, curveHook(opts));
  return { norm, jobs, warnings };
}

/** Python's api._clean: the normalized spec without plotkit's internal "_" keys. */
function clean(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(clean);
  if (isObj(v)) return Object.fromEntries(Object.entries(v).filter(([k]) => !k.startsWith("_")).map(([k, x]) => [k, clean(x)]));
  return v;
}

/** Check a spec against the data without drawing (files, sheets and columns are read; data_code runs).
 *  Returns {ok, kind, spec (normalized), warnings, not_done}; throws PlotkitError(message, hint). */
export async function validate(spec: unknown, files: InputFile[], opts: Options = {}) {
  const [kind, s] = await route(spec, files);
  if (kind === "chart") {
    const { norm, spec: s2, frame } = await chartInput(s, files, opts);
    const model = charts.layout(s2, charts.buildModel(s2, frame));
    return { ok: true as const, kind, spec: clean(norm), warnings: [...model.notes] as string[], not_done: curves.notDone(norm) };
  }
  const { norm, warnings } = await curveInput(s, files, opts);
  return { ok: true as const, kind, spec: clean(norm), warnings, not_done: curves.notDone(norm) };
}

/** The live ECharts options of a spec, one per figure, without drawing files: labels tied to the data, tooltip and
 *  zoom. Chart options may hold "__fmt__..." / "__histbar__" / "__errorbar__" markers: call revive(option) before
 *  setOption. Returns {ok, kind, engine, options, saved: [], warnings, not_done, values, ...}. */
export async function echartsOptions(spec: unknown, files: InputFile[], opts: Options = {}) {
  const [kind, s] = await route(spec, files);
  if (kind === "chart") {
    const { spec: s2, frame } = await chartInput(s, files, opts);
    if (truthy(s2.code)) throw new PlotkitError(...CHART_CODE);
    return charts.liveResult(s2, frame, validatePatch) as any;
  }
  const { norm, jobs, warnings } = await curveInput(s, files, opts);
  return curves.liveResult(norm as any, jobs as any, warnings) as any;
}

export interface SvgFile { name: string; svg: string; width: number; height: number; size_in: number[]; dpi: number }

/** The static figures as SVG (the app turns them into PNG/PDF: sharp, printToPDF). name: the file name without
 *  extension plotkit would give it. Returns {ok, kind, engine, files, warnings, not_done, values, ...}. */
export async function renderSvg(spec: unknown, files: InputFile[], opts: Options & { onChart?: OnChart } = {}) {
  const [kind, s] = await route(spec, files);
  if (kind === "chart") {
    const { spec: s2, frame } = await chartInput(s, files, opts);
    if (truthy(s2.code)) throw new PlotkitError(...CHART_CODE);
    const model = charts.layout(s2, charts.buildModel(s2, frame));
    const [, [W, H]] = charts.echartsOption(s2, model, false);
    const svg = renderChartSvg(s2, model, validatePatch,
      opts.onChart && ((chart, info) => opts.onChart!(chart, { ...info, size_in: s2.size, dpi: s2.dpi, index: 0 })));
    const warnings = [...model.notes] as string[];
    const values = charts.summaryValues(model);
    const notDone = curves.notDone(s2);
    const yc = truthy(s2.y?.col) ? s2.y.col : truthy(s2.x?.col) ? s2.x.col : "chart";     // Python: a or b or "chart"
    let name = truthy(s2.output?.name) ? String(s2.output.name)
      : `${model.kind}_` + Array.from(pyStrValue(yc).replace(/[^\p{L}\p{N}_가-힣]+/gu, "_")).slice(0, 40).join("");
    name = name.replace(/[\\/:*?"<>|\s]+/g, "_").replace(/^_+|_+$/g, "") || "chart";
    return { ok: true as const, kind, engine: "echarts" as const,
      files: [{ name, svg, width: W, height: H, size_in: s2.size, dpi: s2.dpi }] as SvgFile[], warnings, not_done: notDone,
      values, chart: model.kind, rows_used: model.rows_used, rows_total: model.rows_total,
      summary: charts.koreanSummary(model, values, [], notDone, warnings) };
  }
  const { norm, jobs, warnings } = await curveInput(s, files, opts);
  const r = renderCurves(norm as any, jobs as any, warnings, opts.onChart);
  return { ok: true as const, kind, engine: "echarts" as const,
    files: r.files.map(f => ({ name: f.stem, svg: f.svg, width: f.W, height: f.H, size_in: f.size_in, dpi: f.dpi })) as SvgFile[],
    warnings: r.warnings, not_done: r.not_done, values: r.values, plots: r.plots };
}
