// A chart's static SVG, as plotkit/js/render_chart.mjs draws it: ECharts server-side rendering of the option with
// its markers revived (no files written: the caller saves or converts the string).
import * as echarts from "echarts";
import { revive } from "./revive.ts";
import { applyPatch, echartsOption, type ChartModel, type ChartSpec, type EChartsOption, type ValidatePatch } from "./charts.ts";

/** The SVG of an ECharts option on a width x height px canvas (rounded as the Node renderer rounds them). */
export function renderSvg(option: EChartsOption, width: number, height: number,
  onChart?: (chart: echarts.ECharts, info: { W: number; H: number }) => void): string {
  const W = Math.round(Number(width) || 640), H = Math.round(Number(height) || 460);
  const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: W, height: H });
  try {
    chart.setOption(revive(structuredClone(option)));
    onChart?.(chart, { W, H });
    return freshIds(chart.renderToSVGString());
  } finally {
    chart.dispose();
  }
}

/** zrender numbers SVG painters (zr0, zr1, ...) and CSS classes (zrN-cls-K) process-wide; the Node renderer draws
 *  each chart in a new process. Renumber as a fresh process would, so the same chart gives the same SVG (ids are
 *  then not unique across charts: give each SVG its own document, or rename them before inlining several). */
function freshIds(svg: string): string {
  const cls = [...svg.matchAll(/\bzr\d+-cls-(\d+)\b/g)].map(m => Number(m[1]));
  const base = cls.length ? Math.min(...cls) : 0;
  return svg.replace(/\bzr\d+-cls-(\d+)\b/g, (_, n: string) => `zr0-cls-${Number(n) - base}`).replace(/\bzr\d+-/g, "zr0-");
}

/** A chart's exported SVG (plotkit.charts.draw_echarts): the static option with the spec's "echarts" patch merged. */
export function renderChartSvg(spec: ChartSpec, model: ChartModel, validatePatch?: ValidatePatch,
  onChart?: (chart: echarts.ECharts, info: { W: number; H: number }) => void): string {
  const [opt, [W, H]] = echartsOption(spec, model);
  return renderSvg(applyPatch(spec, opt, validatePatch), W, H, onChart);
}
