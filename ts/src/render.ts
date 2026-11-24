// The static render of resolved curve figures: ECharts server-side SVG, labels laid out in pixels. A port of the
// SVG step of plotkit/js/render.mjs; the host turns the SVG into PNG or PDF itself (KetchupE: sharp / printToPDF).
import * as echarts from "echarts";
import { bestPlace, buildOption, layout, legendOption, lineTexts, mergePatch, placeLabels } from "./translate.ts";
import type { Box } from "./translate.ts";
import { curveValues, fileStem, notDone, resolve, truthy } from "./curves.ts";
import type { AnnotationResult, CurveSpec, Figure, Job } from "./curves.ts";
import { PlotkitError } from "./errors.ts";

export interface Rendered { svg: string; warnings: string[]; W: number; H: number }

/** Called with the drawn ECharts instance before it is turned into SVG (the experiments' figure-facts checker
 *  reads it there, as render.mjs's PLOTKIT_DUMP_OPTION did). */
export type OnChart = (chart: echarts.ECharts, info: { W: number; H: number; size_in: number[]; dpi: number; index: number }) => void;

/** One figure -> SVG text with zrender's ids as they come (the painter's id: "zrN"). */
function renderRaw(figure: Figure, onChart?: OnChart, index = 0): Rendered & { zrId: string | null } {
  // Python's plot_echarts tells the renderer how many series the figure has (the "echarts" patch is checked on it)
  const fig: Figure = figure.n_series === undefined ? { ...figure, n_series: figure.series.length } : figure;
  const warnings: string[] = [];
  const L = layout(fig);
  if (fig.tick_direction === "inout") warnings.push('tick_direction "inout" has no ECharts setting; drawn as longer outward ticks');
  let option = buildOption(fig, L);
  option = mergePatch(option, fig.echarts, fig);
  const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: L.W, height: L.H });
  try {
    chart.setOption(option);
    const toPixel = (a: { axis?: string; x?: number; y?: number }): number[] =>
      chart.convertToPixel({ xAxisIndex: L.split && a.axis === "y2" ? 1 : 0, yAxisIndex: a.axis === "y2" ? 1 : 0 }, [a.x!, a.y!]) as number[];
    let legendBox: Box | null = null;
    if (fig.legend.show && !(fig.echarts && fig.echarts.legend)) {
      let where = fig.legend.where;
      if (where === "best") {
        const pts: number[][] = [];
        for (const s of fig.series) {
          const step = Math.max(1, Math.floor(s.points.length / 400));
          for (let i = 0; i < s.points.length; i += step) pts.push(toPixel({ axis: s.axis, x: s.points[i][0], y: s.points[i][1] }));
        }
        where = bestPlace(fig, L, pts);
        const lg = legendOption(fig, L, where);
        delete lg._box;
        chart.setOption({ legend: lg });
      }
      legendBox = legendOption(fig, L, where)._box as Box;
    }
    const graphics = [
      ...lineTexts(fig, L, toPixel),
      ...placeLabels(fig, L, toPixel, legendBox ? [legendBox] : []),
      ...((fig.echarts && fig.echarts.graphic) || []),
    ];
    if (graphics.length) chart.setOption({ graphic: { elements: graphics } });
    onChart?.(chart, { W: L.W, H: L.H, size_in: fig.size_in, dpi: fig.dpi, index });
    let svg = chart.renderToSVGString();
    // a real size in the file, so other programs (Word, PowerPoint, Inkscape) open it at the asked inches
    svg = svg.replace(/^<svg /, `<svg data-plotkit-dpi="${fig.dpi}" `);
    const zrId = (chart.getZr() as unknown as { painter?: { _id?: unknown } }).painter?._id;
    return { svg, warnings, W: L.W, H: L.H, zrId: typeof zrId === "string" ? zrId : null };
  } finally {
    chart.dispose();
  }
}

/** zrender numbers its SVG ids with counters global to the process ("zr<painter>-c0", "zr<painter>-cls-<class>").
 *  render.mjs ran in a fresh Node process per call, so figure i of a call is painter i and the CSS classes count
 *  from 0 over the call; renumber to that, so the SVG text is the same as the Python plotkit's. */
function renumber(svg: string, zrId: string | null, index: number, classes: { next: number }): string {
  const own = zrId ?? /zr\d+(?=-)/.exec(svg)?.[0];
  if (!own) return svg;
  const esc = own.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const used = new Set<number>();
  for (const m of svg.matchAll(new RegExp(`${esc}-cls-(\\d+)`, "g"))) used.add(Number(m[1]));
  const map = new Map([...used].sort((a, b) => a - b).map(c => [c, classes.next++]));
  return svg.replace(new RegExp(`${esc}-(?:cls-(\\d+))?`, "g"), (_m, c?: string) =>
    `zr${index}-` + (c === undefined ? "" : `cls-${map.get(Number(c))}`));
}

/** Every figure's SVG (W x H px at 96 px per inch, with data-plotkit-dpi) and warnings, in order: render.mjs's loop
 *  without writing files. The ids are numbered as one render.mjs call numbers them (figure i: "zr<i>-..."). */
export function renderSvgs(figures: Figure[], onChart?: OnChart): Rendered[] {
  const classes = { next: 0 };
  return figures.map((fig, i) => {
    const { zrId, ...r } = renderRaw(fig, onChart, i);
    return { ...r, svg: renumber(r.svg, zrId, i, classes) };
  });
}

/** One resolved figure -> SVG text and warnings (numbered as the only figure of a call). */
export function renderSvg(figure: Figure): Rendered {
  return renderSvgs([figure])[0];
}

/** One drawn figure of renderCurves: its file name without extension (plotkit.core.file_stem) and SVG. */
export interface CurveFile extends Rendered { stem: string; size_in: number[]; dpi: number }

/** One figure's facts in the result (plot_echarts's "plots", without saved paths). */
export interface CurvePlot {
  sheet: string; file: string; stem: string; rows_plotted: number;
  columns_used: Record<string, Record<string, string>>; column_guess: string; annotations: AnnotationResult[];
}

/** plotkit.echarts.plot_echarts after normalize_spec and build_jobs, without writing files: every figure's SVG (the
 *  host converts and saves it, e.g. as stem + ".png") and the shared result {ok, kind, engine, saved: [], warnings
 *  (the render's added), not_done, values, plots}. */
export function renderCurves(spec: CurveSpec, jobs: Job[], warnings: string[] = [], onChart?: OnChart): {
  ok: true; kind: "curve"; engine: "echarts"; files: CurveFile[]; saved: string[]; warnings: string[];
  not_done: string[]; values: Record<string, Record<string, unknown>>; plots: CurvePlot[];
} {
  if (truthy(spec.code)) {
    throw new PlotkitError('"code" (Python) does not work with the ECharts engine',
      'use a key (e.g. annotate band for shading), or put ECharts settings in "echarts"');
  }
  const out = [...warnings];
  const nameTpl = (truthy(spec.output?.name) ? spec.output!.name : spec.file.length > 1 ? "{file}_{sheet}" : "{sheet}") as string;
  const figs = resolve(spec, jobs);
  const drawn = renderSvgs(figs.map(f => ({ ...f.figure, n_series: f.figure.series.length })), onChart);
  const files: CurveFile[] = [], plots: CurvePlot[] = [];
  figs.forEach(({ group, figure, annotations }, i) => {
    const first = group[0];
    const stem = fileStem(nameTpl, spec, first);
    for (const w of drawn[i].warnings) if (!out.includes(w)) out.push(w);
    files.push({ ...drawn[i], stem, size_in: figure.size_in, dpi: figure.dpi });
    plots.push({
      sheet: truthy(spec.combine) ? "all" : first.sheet,
      file: first.file.split("/").filter(Boolean).at(-1) ?? "",
      stem,
      rows_plotted: group.reduce((n, j) => n + j.rows, 0),
      columns_used: Object.fromEntries(group.map(j => [j.sheet, Object.fromEntries(Object.entries(j.cols).map(([r, c]) => [r, `${c.letter} "${c.name}"`]))])),
      column_guess: (truthy(first.how) ? first.how : "as given"),
      annotations,
    });
  });
  return { ok: true, kind: "curve", engine: "echarts", files, saved: [], warnings: out, not_done: notDone(spec),
    values: curveValues(plots), plots };
}
