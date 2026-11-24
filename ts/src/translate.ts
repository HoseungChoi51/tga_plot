// Resolved figure (curves.resolve) -> ECharts option, and the label layout. A port of plotkit/js/translate.mjs: the
// same arithmetic in the same order, so the options and the SVG are the same as the Python plotkit's.
// The model's "echarts" patch is plain JSON, already checked against an allowlist when the spec was normalized, and
// is merged by mergePatch() below.
import { PlotkitError } from "./errors.ts";
import type { Figure, FigureAnnotation, FigureAxis, FigureSeries } from "./curves.ts";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Option = Record<string, any>;
export type Box = [number, number, number, number];
export type ToPixel = (a: { axis?: string; x?: number; y?: number }) => number[];

export const PT = 96 / 72;            // points -> px; the SVG is laid out at 96 px per inch

const CJK = /[ᄀ-ᇿ㄰-㆏가-힯぀-ヿ一-鿿]/;

/** Rough text width in px. SSR has no font metrics, so this is an estimate (good to ~10 %). */
export function textWidth(text: unknown, sizePx: number, bold = false): number {
  let w = 0;
  for (const ch of String(text ?? "")) {
    if (CJK.test(ch)) w += 1.0;
    else if (ch === " ") w += 0.32;
    else if ("il.,:;'|!()[]".includes(ch)) w += 0.33;
    else if (/[A-Z0-9%°]/.test(ch)) w += 0.66;
    else w += 0.56;
  }
  return w * sizePx * (bold ? 1.07 : 1);
}

export function textBox(text: unknown, sizePx: number, bold = false): { w: number; h: number } {
  const lines = String(text ?? "").split("\n");
  return { w: Math.max(...lines.map(l => textWidth(l, sizePx, bold))), h: lines.length * sizePx * 1.2 };
}

/** matplotlib's ScalarFormatter look: the same number of decimals on every tick. */
export function tickFormatter(ticks: number[] | null | undefined): (v: number) => string {
  const dec = Math.min(6, Math.max(0, ...(ticks ?? []).map(v => {
    const s = String(Number(v.toPrecision(10)));
    return s.includes("e") ? 0 : (s.split(".")[1] ?? "").length;
  })));
  return v => (Math.abs(v) < 1e-12 ? 0 : v).toFixed(dec);
}

// matplotlib dash patterns, in units of the line width
const DASH: Record<string, "solid" | number[]> = { solid: "solid", dashed: [3.7, 1.6], dotted: [1, 1.65], dashdot: [6.4, 1.6, 1, 1.6] };
export function dash(style: string, widthPx: number): "solid" | number[] {
  const d = (Object.hasOwn(DASH, style) ? DASH[style] : undefined) ?? "solid";
  return Array.isArray(d) ? d.map(v => v * Math.max(widthPx, 1)) : d;
}

/** Where plotkit's legend positions land, relative to the plot area. */
const PLACES: Record<string, [number, number]> = {
  "upper right": [1, 0], "upper left": [0, 0], "lower left": [0, 1], "lower right": [1, 1],
  "right": [1, 0.5], "center left": [0, 0.5], "center right": [1, 0.5], "lower center": [0.5, 1],
  "upper center": [0.5, 0], "center": [0.5, 0.5],
};
const BEST_ORDER = ["upper right", "upper left", "lower left", "lower right", "right", "center left",
  "center right", "lower center", "upper center", "center"];

export interface Area { x0: number; y0: number; x1: number; y1: number }
export interface Layout {
  W: number; H: number; tickLen: number; pad: number; labelPad: number; margin: number; out: boolean;
  split: boolean;
  grid: { left: number; right: number; top: number; bottom: number };
  area: Area;
  nameGap: { x: number; y1: number; y2: number };
  grids?: { left: number; right: number; top: number; height: number }[];
  areas?: Area[];
}

export function layout(fig: Figure): Layout {
  const W = fig.size_in[0] * 96, H = fig.size_in[1] * 96;
  const fpx = (pt: number) => pt * PT;
  const tickLen = 3.5 * PT, pad = 3.5 * PT, labelPad = 4 * PT;
  const out = fig.tick_direction !== "in";
  const ax = fig.axes;
  const tickW = (a: FigureAxis | null) => {
    if (!a) return 0;
    const f = tickFormatter(a.ticks);
    const vals = a.ticks ?? [a.min, a.max];
    return Math.max(...vals.map(v => textWidth(f(v), fpx(a.tick_size))));
  };
  const margin = (out ? tickLen : 0) + pad;
  const split = !!(fig.panels === "split" && ax.y2);
  const yw = split ? Math.max(tickW(ax.y1), tickW(ax.y2)) : tickW(ax.y1);
  const left = margin + yw + labelPad + fpx(Math.max(ax.y1.label_size, split ? ax.y2!.label_size : 0)) * 1.2 + 8;
  let right = ax.y2 && !split ? margin + tickW(ax.y2) + labelPad + fpx(ax.y2.label_size) * 1.2 + 8 : 18;
  let bottom = margin + fpx(ax.x.tick_size) * 1.2 + labelPad + fpx(ax.x.label_size) * 1.2 + 8;
  const top = fig.title.text ? fpx(fig.title.size) * 1.2 * fig.title.text.split("\n").length + 14 : 14;
  const where = fig.legend.show ? fig.legend.where : null;
  if (where === "outside right") right += legendBox(fig).w + 16;
  if (where === "outside bottom") bottom += legendBox(fig).sizePx * 1.8 + 8;
  const L: Layout = {
    W, H, tickLen, pad, labelPad, margin, out, split,
    grid: { left, right, top, bottom },
    area: { x0: left, y0: top, x1: W - right, y1: H - bottom },
    nameGap: { x: margin + fpx(ax.x.tick_size) * 1.2 + labelPad, y1: margin + yw + labelPad, y2: margin + (split ? yw : tickW(ax.y2)) + labelPad },
  };
  if (split) {                            // y1 above, y2 below, one x axis at the bottom
    const h = H - top - bottom, gap = 10, h1 = (h - gap) * 1.25 / 2.25;
    L.grids = [{ left, right, top, height: h1 }, { left, right, top: top + h1 + gap, height: h - h1 - gap }];
    L.areas = [{ x0: left, y0: top, x1: W - right, y1: top + h1 }, { x0: left, y0: top + h1 + gap, x1: W - right, y1: H - bottom }];
    L.area = L.areas[0];                  // the legend and the top labels live in the upper panel
  }
  return L;
}

function axisOption(a: FigureAxis, L: Layout, fig: Figure, which: "x" | "y1" | "y2", nameGap: number, position?: string): Option {
  const fmt = tickFormatter(a.ticks);
  const tickLine = { color: a.tick_mark_color, width: 0.8 * PT };
  const inout = fig.tick_direction === "inout";
  const opt: Option = {
    type: a.log ? "log" : "value", min: a.min, max: a.max, scale: true,
    name: a.label, nameLocation: "middle", nameGap,
    nameTextStyle: { color: a.label_color, fontSize: a.label_size * PT, fontFamily: fig.font_family },
    axisLine: { show: true, onZero: false, lineStyle: { color: a.line_color ?? "#000000", width: 0.8 * PT } },
    axisTick: { show: true, inside: fig.tick_direction === "in", length: inout ? 2 * L.tickLen : L.tickLen, lineStyle: tickLine },
    axisLabel: { show: true, color: a.tick_color, fontSize: a.tick_size * PT, fontFamily: fig.font_family, margin: L.margin,
      formatter: a.log ? undefined : fmt, showMinLabel: true, showMaxLabel: true },
    splitLine: { show: fig.grid && which !== "y2", lineStyle: { color: "rgba(176,176,176,0.3)", width: 0.8 * PT } },
    inverse: !!a.inverse,
    minorTick: { show: !!a.minor, splitNumber: 5, length: L.tickLen * 0.55, lineStyle: tickLine },
  };
  if (a.ticks) {
    opt.axisTick.customValues = a.ticks;
    opt.axisLabel.customValues = a.ticks;
  }
  if (which !== "x") {
    opt.position = position;
    opt.nameRotate = 90;
  }
  return opt;
}

function seriesOption(s: FigureSeries, axisIndex: number): Option {
  const w = s.width * PT;
  if (s.style === "scatter") {
    return { type: "scatter", name: s.name, yAxisIndex: axisIndex, data: s.points, symbolSize: 3.8,
      itemStyle: { color: s.color }, silent: true, animation: false };
  }
  return { type: "line", name: s.name, yAxisIndex: axisIndex, data: s.points, color: s.color,
    showSymbol: s.style === "line+marker", symbol: s.style === "line+marker" ? "circle" : "none", symbolSize: 4,
    lineStyle: { color: s.color, width: w, type: dash(s.linestyle, w) }, itemStyle: { color: s.color },
    silent: true, animation: false, clip: true, sampling: undefined, z: 2 };
}

export function legendBox(fig: Figure): { names: string[]; sizePx: number; itemW: number; gap: number; w: number; h: number } {
  const lg = fig.legend;
  const names = [...lg.names, ...lg.extra.map(e => e.name)];
  const sizePx = lg.size * PT;
  const itemW = 2 * sizePx, gap = 0.5 * sizePx;
  const w = itemW + 0.8 * sizePx + Math.max(...names.map(n => textWidth(n, sizePx)));
  const h = names.length * sizePx * 1.25 + Math.max(0, names.length - 1) * gap;
  return { names, sizePx, itemW, gap, w, h };
}

/** Legend placed inside the plot area like matplotlib's loc=..., with a 0.5 em border pad. */
export function legendOption(fig: Figure, L: Layout, where: string): Option {
  const lg = fig.legend;
  if (!lg.show) return { show: false };
  const b = legendBox(fig);
  const base = {
    padding: 0, itemGap: b.gap, itemWidth: b.itemW, itemHeight: b.sizePx * 0.8,
    textStyle: { color: lg.color, fontSize: b.sizePx, fontFamily: fig.font_family },
    data: b.names, selectedMode: false, itemStyle: { opacity: 0 },
  };
  if (where === "outside right") {
    const x0 = L.W - b.w - 10, y0 = L.area.y0 + (L.area.y1 - L.area.y0 - b.h) / 2;
    return { show: true, orient: "vertical", left: x0, top: y0, ...base, _box: [x0, y0, x0 + b.w, y0 + b.h] };
  }
  if (where === "outside bottom") {
    const y0 = L.H - b.sizePx * 1.6 - 4;
    return { show: true, orient: "horizontal", left: "center", top: y0, ...base, _box: [0, y0, L.W, L.H] };
  }
  const [fx, fy] = (Object.hasOwn(PLACES, where) ? PLACES[where] : undefined) ?? PLACES["center left"];
  const inset = 0.6 * b.sizePx;
  const A = L.area, aw = A.x1 - A.x0, ah = A.y1 - A.y0;
  const x0 = A.x0 + inset + fx * (aw - 2 * inset - b.w);
  const y0 = A.y0 + inset + fy * (ah - 2 * inset - b.h);
  return {
    show: true, orient: "vertical", left: x0, top: y0, padding: 0, itemGap: b.gap, itemWidth: b.itemW, itemHeight: b.sizePx * 0.8,
    textStyle: { color: lg.color, fontSize: b.sizePx, fontFamily: fig.font_family },
    data: b.names, selectedMode: false,
    itemStyle: { opacity: 0 },             // line keys only, no marker dot (matplotlib's look)
    _box: [x0, y0, x0 + b.w, y0 + b.h],
  };
}

/** matplotlib's loc="best": the candidate position that covers the fewest data points. */
export function bestPlace(fig: Figure, L: Layout, pixelPoints: number[][]): string {
  let best = BEST_ORDER[0], fewest = Infinity;
  for (const where of BEST_ORDER) {
    const [x0, y0, x1, y1] = legendOption(fig, L, where)._box as Box;
    let n = 0;
    for (const [px, py] of pixelPoints) if (px >= x0 && px <= x1 && py >= y0 && py <= y1) n++;
    if (n < fewest) { fewest = n; best = where; }
  }
  return best;
}

export function buildOption(fig: Figure, L: Layout): Option {
  const ax = fig.axes;
  const yAxis = [axisOption(ax.y1, L, fig, "y1", L.nameGap.y1, "left")];
  if (ax.y2) yAxis.push(axisOption(ax.y2, L, fig, "y2", L.nameGap.y2, L.split ? "left" : "right"));
  const series: Option[] = fig.series.map(s => seriesOption(s, s.axis === "y2" ? 1 : 0));
  if (L.split) {
    yAxis[1].gridIndex = 1;
    yAxis[1].splitLine.show = !!fig.grid;
    for (const s of series) if (s.yAxisIndex === 1) s.xAxisIndex = 1;
  }
  for (const e of fig.legend.extra) {      // gray "Weight / Deriv." keys when sheets are combined
    series.push({ type: "line", name: e.name, data: [], yAxisIndex: 0, color: e.color, symbol: "none",
      lineStyle: { color: e.color, width: 1.5 * PT, type: dash(e.linestyle, 1.5 * PT) }, silent: true, animation: false });
  }
  // vertical/horizontal lines and bands ride on helper series after the data series,
  // so the model's series[0] / series[1] stay y1 / y2.
  const marks: Record<string, { line: Option[]; area: Option[][] }> = { y1: { line: [], area: [] }, y2: { line: [], area: [] } };
  for (const a of fig.annotations) {
    if (a.kind === "vline") marks.y1.line.push({ xAxis: a.value, lineStyle: { color: a.color, width: 0.9 * PT, type: dash(a.linestyle!, 0.9 * PT) } });
    if (a.kind === "hline") marks[a.axis!].line.push({ yAxis: a.value, lineStyle: { color: a.color, width: 0.9 * PT, type: dash(a.linestyle!, 0.9 * PT) } });
    if (a.kind === "band") marks.y1.area.push([{ xAxis: a.x_min, itemStyle: { color: a.fill } }, { xAxis: a.x_max }]);
  }
  for (const [axis, m] of Object.entries(marks)) {
    if (!m.line.length && !m.area.length) continue;
    series.push({ type: "line", name: `__marks_${axis}`, data: [], yAxisIndex: axis === "y2" ? 1 : 0,
      xAxisIndex: L.split && axis === "y2" ? 1 : 0, silent: true, animation: false,
      markLine: m.line.length ? { silent: true, symbol: "none", label: { show: false }, animation: false, data: m.line } : undefined,
      markArea: m.area.length ? { silent: true, label: { show: false }, animation: false, data: m.area, z: 0 } : undefined, z: 1 });
  }
  const legend = legendOption(fig, L, fig.legend.where === "best" ? "upper right" : fig.legend.where);
  delete legend._box;
  return {
    animation: false, backgroundColor: "#ffffff",
    textStyle: { fontFamily: fig.font_family, color: fig.text_color, fontSize: fig.font_size * PT },
    title: fig.title.text ? { text: fig.title.text, left: "center", top: 6,
      textStyle: { color: fig.title.color, fontSize: fig.title.size * PT, fontWeight: "normal", fontFamily: fig.font_family } } : { show: false },
    grid: L.split ? L.grids!.map(g => ({ ...g, show: true, borderColor: "#000000", borderWidth: 0.8 * PT, backgroundColor: "transparent", containLabel: false }))
      : { ...L.grid, show: true, borderColor: "#000000", borderWidth: 0.8 * PT, backgroundColor: "transparent", containLabel: false },
    xAxis: L.split ? [{ ...axisOption(ax.x, L, fig, "x", L.nameGap.x), gridIndex: 0, name: "", axisLabel: { show: false } },
      { ...axisOption(ax.x, L, fig, "x", L.nameGap.x), gridIndex: 1 }] : axisOption(ax.x, L, fig, "x", L.nameGap.x),
    yAxis, series, legend,
  };
}

const isObj = (v: unknown): v is Option => !!v && typeof v === "object" && !Array.isArray(v);
function deepMerge(base: any, over: any): any {
  if (!isObj(base) || !isObj(over)) return structuredClone(over);
  const out: Option = { ...base };
  for (const [k, v] of Object.entries(over)) {
    if ((k === "markLine" || k === "markArea" || k === "markPoint") && isObj(v)) {
      const prev = isObj(out[k]) ? out[k] : {};
      out[k] = { ...deepMerge(prev, { ...v, data: undefined }), data: [...(prev.data ?? []), ...(v.data ?? [])] };
      if (!out[k].data.length) delete out[k].data;
    } else if (v === undefined) {
      continue;
    } else out[k] = isObj(v) && isObj(out[k]) ? deepMerge(out[k], v) : structuredClone(v);
  }
  return out;
}

/** The model's "echarts" patch: objects merge, lists (yAxis, series) merge by index, graphic is added. */
export function mergePatch(option: Option, patch: Option | null | undefined, fig: Figure): Option {
  if (!patch) return option;
  const o: Option = { ...option };
  for (const [k, v] of Object.entries(patch)) {
    if (k === "graphic") continue;
    if (k === "series" || k === "yAxis") {
      const list = Array.isArray(o[k]) ? [...o[k]] : [o[k]];
      const limit = k === "series" ? fig.n_series : list.length;
      if (v.length > (limit as number)) {
        const what = k === "series" ? fig.series.map((s, i) => `${i} = ${s.axis} ${s.sheet ?? ""}`.trim()).join(", ")
          : "0 = y1 (left)" + (list.length > 1 ? ", 1 = y2 (right)" : "");
        throw new PlotkitError(`echarts.${k} has ${v.length} entries but this plot has ${limit}`, `${k}: ${what}`);
      }
      (v as any[]).forEach((item, i) => { if (item && Object.keys(item).length) list[i] = deepMerge(list[i], item); });
      o[k] = list;
    } else if (k === "xAxis" && Array.isArray(v)) {
      o.xAxis = deepMerge(o.xAxis, v[0] ?? {});
    } else o[k] = isObj(v) ? deepMerge(o[k] ?? {}, v) : structuredClone(v);
  }
  return o;
}

/* ------------------------------------------------------------------ label layout
 * A port of plotkit._place_labels in screen pixels (y grows downwards): residue labels sit
 * 40 pt above (or below) their point with a leader line; several of them form a column; peak
 * labels sit just above their peak and move only as far as needed to clear what is drawn. */
export function placeLabels(fig: Figure, L: Layout, toPixel: ToPixel, obstacles: Box[]): Option[] {
  const els: Option[] = [];
  const A = L.area;
  const pt = PT, gap = 2 * pt;
  const boxes: Box[] = obstacles.map(b => [...b] as Box);
  const family = fig.font_family;
  const hits = (b: Box) => boxes.filter(o => b[0] < o[2] + gap && o[0] < b[2] + gap && b[1] < o[3] + gap && o[1] < b[3] + gap);
  const extent = (lab: FigureAnnotation, bold = false, padF = 0.25) => {
    const s = lab.size * PT, t = textBox(lab.text, s, bold), p = padF * s;
    return { w: t.w + 2 * p, h: t.h + 2 * p, pad: p };
  };
  const shift = (b: Box, dx: number, dy: number): Box => [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy];
  function clear(b: Box, down: boolean): [number, number] {             // down: move towards larger y
    let v: Box = [...b];
    for (let i = 0; i <= boxes.length; i++) {
      const h = hits(v);
      if (!h.length) break;
      const s = down ? Math.max(...h.map(o => o[3])) + gap - v[1] : Math.min(...h.map(o => o[1])) - gap - v[3];
      v = shift(v, 0, s);
    }
    const dy = v[1] - b[1];
    if (!dy || (down ? v[3] <= A.y1 : v[1] >= A.y0)) return [0, dy];
    let best: number | null = null;
    for (const side of [-1, 1]) {
      let h: Box = [...b];
      for (let i = 0; i <= boxes.length; i++) {
        const hit = hits(h);
        if (!hit.length) break;
        const s = side < 0 ? Math.min(...hit.map(o => o[0])) - gap - h[2] : Math.max(...hit.map(o => o[2])) + gap - h[0];
        h = shift(h, s, 0);
      }
      if (!hits(h).length && h[0] >= A.x0 && h[2] <= A.x1 && (best === null || Math.abs(h[0] - b[0]) < Math.abs(best))) best = h[0] - b[0];
    }
    return best !== null ? [best, 0] : [0, dy];
  }
  const text = (lab: FigureAnnotation, b: Box, pad: number, color: string | undefined, bold: boolean, align = "left", boxed = true) => {
    if (boxed) els.push({ type: "rect", z: 100, silent: true, shape: { x: b[0], y: b[1], width: b[2] - b[0], height: b[3] - b[1], r: 0.25 * lab.size * PT },
      style: { fill: "rgba(255,255,255,0.85)", stroke: "none" } });
    const x = align === "left" ? b[0] + pad : align === "right" ? b[2] - pad : (b[0] + b[2]) / 2;
    els.push({ type: "text", z: 101, silent: true, x, y: b[1] + pad,
      style: { text: lab.text, fill: color, fontSize: lab.size * PT, fontFamily: family, fontWeight: bold ? "bold" : "normal",
        lineHeight: lab.size * PT * 1.2, align, verticalAlign: "top" } });
  };
  const line = (x1: number, y1: number, x2: number, y2: number, color: string | undefined, w: number) =>
    els.push({ type: "line", z: 99, silent: true, shape: { x1, y1, x2, y2 }, style: { stroke: color, lineWidth: w } });
  const toward = (b: Box, px: number, py: number) => [Math.min(Math.max(px, b[0]), b[2]), Math.min(Math.max(py, b[1]), b[3])];

  // markers first (under the labels)
  for (const a of fig.annotations) {
    if (a.kind !== "value" && a.kind !== "peak") continue;
    const [px, py] = toPixel(a);
    if (a.kind === "value") {
      els.push({ type: "circle", z: 98, silent: true, shape: { cx: px, cy: py, r: 3 * pt }, style: { fill: "#ffffff", stroke: a.color, lineWidth: 1.6 * pt } });
    } else {
      const r = 3 * pt, s = a.down ? -1 : 1;
      els.push({ type: "polygon", z: 98, silent: true, shape: { points: [[px, py - s * r], [px - r, py + s * r * 0.8], [px + r, py + s * r * 0.8]] }, style: { fill: a.color } });
    }
  }

  // residue labels and "no data" notes, grouped per axis and name
  const groups = new Map<string, FigureAnnotation[]>();
  for (const a of fig.annotations) {
    if (a.kind !== "value" && a.kind !== "note") continue;
    const key = `${a.axis}|${a.name}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(a);
  }
  for (const grp of groups.values()) {
    const data = grp.filter(l => l.kind === "value"), notes = grp.filter(l => l.kind === "note");
    if (!data.length) {
      for (const lab of notes) {
        const { w, h, pad } = extent(lab, false, 0.3);
        const xr = A.x0 + 0.98 * (A.x1 - A.x0), yc = A.y0 + (0.5 + 0.09 * lab.stack!) * (A.y1 - A.y0);
        const b: Box = [xr + pad - w, yc - h / 2, xr + pad, yc + h / 2];
        text(lab, b, pad, lab.color, false, "right");
        boxes.push(b);
      }
      continue;
    }
    const pts = new Map(data.map(l => [l, toPixel(l)]));
    const up = Math.max(...data.map(l => (A.y1 - pts.get(l)![1]) / (A.y1 - A.y0))) < 0.7;
    const placeAt = (lab: FigureAnnotation, xt: number, yt: number, ha: string): Box => {      // (xt, yt): text anchor; box above it when up
      const { w, h, pad } = extent(lab);
      const x0 = ha === "right" ? xt + pad - w : ha === "left" ? xt - pad : xt - w / 2;
      const y1 = up ? yt + pad : yt - pad + h;
      return [x0, y1 - h, x0 + w, y1];
    };
    if (data.length === 1 && !notes.length) {
      const lab = data[0], [px, py] = pts.get(lab)!;
      const fx = (px - A.x0) / (A.x1 - A.x0);
      const ha = fx > 0.8 ? "right" : fx < 0.2 ? "left" : "center";
      let xt = px + (ha === "right" ? 12 : ha === "left" ? -12 : 0) * pt;
      const yt = py + (up ? -40 : 40) * pt;
      let b = placeAt(lab, xt, yt, ha);
      xt += Math.max(0, A.x0 + gap - b[0]) - Math.max(0, b[2] - (A.x1 - gap));
      b = placeAt(lab, xt, yt, ha);
      const [dx, dy] = clear(b, !up);
      b = shift(b, dx, dy);
      const [lx, ly] = toward(b, px, py);
      line(lx, ly, px, py, lab.color, 0.8 * pt);
      text(lab, b, extent(lab).pad, lab.text_color, false, ha === "center" ? "center" : ha);
      boxes.push(b);
      continue;
    }
    const width = Math.max(...grp.map(l => extent(l).w));
    const xs = [...pts.values()].map(p => p[0]);
    const right = Math.max(...xs) + 6 * pt, left = Math.min(...xs) - 6 * pt;
    const ha = right + width <= A.x1 || (left - width < A.x0 && A.x1 - right >= left - A.x0) ? "left" : "right";
    const edge = ha === "left" ? right : left;
    const near = [...data].sort((a, b) => up ? pts.get(b)![1] - pts.get(a)![1] : pts.get(a)![1] - pts.get(b)![1]);
    let y = pts.get(near.at(-1)!)![1] + (up ? -40 : 40) * pt;
    for (const lab of [...near, ...notes]) {
      const b = placeAt(lab, edge, y, ha);
      if (lab.kind === "value") {
        const [px, py] = pts.get(lab)!;
        line(ha === "left" ? b[0] : b[2], up ? b[3] : b[1], px, py, lab.color, 0.8 * pt);
      }
      text(lab, b, extent(lab).pad, lab.text_color ?? lab.color, false, ha);
      boxes.push(b);
      y += (up ? -1 : 1) * (b[3] - b[1] + gap);
    }
  }

  // peak labels, lowest peak first
  const peaks = fig.annotations.filter(a => a.kind === "peak").map(a => ({ a, p: toPixel(a) }));
  peaks.sort((u, v) => (u.a.down ? u.p[1] - v.p[1] : v.p[1] - u.p[1]));
  for (const { a: lab, p: [px, py] } of peaks) {
    const { w, h, pad } = extent(lab, true);
    const y0 = lab.down ? py + 11 * pt - pad : py - 9 * pt + pad - h;
    let b: Box = [px - w / 2, y0, px + w / 2, y0 + h];
    const [dx, dy] = clear(b, !!lab.down);
    b = shift(b, dx, dy);
    if (Math.hypot(dx, dy) / pt > 3) {
      const [lx, ly] = toward(b, px, py);
      line(lx, ly, px, py + (lab.down ? 4 * pt : -4 * pt), lab.color, 0.6 * pt);
    }
    text(lab, b, pad, lab.text_color, true, "center", fig.box_peaks);
    boxes.push(b);
  }
  return els;
}

/** Texts of vertical/horizontal lines and bands, and corner notes. */
export function lineTexts(fig: Figure, L: Layout, toPixel: ToPixel): Option[] {
  const els: Option[] = [], A = L.area;
  const t = (x: number, y: number, a: FigureAnnotation, align: string, vAlign: string, color: string | undefined) => els.push({ type: "text", z: 101, silent: true, x, y,
    style: { text: a.text, fill: color, fontSize: a.size * PT, fontFamily: fig.font_family, align, verticalAlign: vAlign } });
  for (const a of fig.annotations) {
    if (a.kind === "vline" && a.text) t(toPixel({ axis: "y1", x: a.value, y: 0 })[0] + 3 * PT, A.y0 + 3 * PT, a, "left", "top", a.text_color);
    if (a.kind === "hline" && a.text) t(A.x0 + 3 * PT, toPixel({ axis: a.axis, x: 0, y: a.value })[1] - 3 * PT, a, "left", "bottom", a.text_color);
    if (a.kind === "band" && a.text) t(toPixel({ axis: "y1", x: (a.x_min! + a.x_max!) / 2, y: 0 })[0], A.y0 + 3 * PT, a, "center", "top", a.text_color);
    if (a.kind === "text_at") {
      const [px, py] = toPixel(a);
      els.push({ type: "circle", z: 98, silent: true, shape: { cx: px, cy: py, r: 2.5 * PT }, style: { fill: a.color } });
      els.push({ type: "rect", z: 100, silent: true, shape: { x: px + 4 * PT, y: py - 5 * PT - a.size * PT * 1.3, width: textWidth(a.text, a.size * PT) + 4, height: a.size * PT * 1.3 },
        style: { fill: "rgba(255,255,255,0.85)" } });
      t(px + 5 * PT, py - 5 * PT, a, "left", "bottom", a.color);
    }
    if (a.kind === "text") {
      const POS: Record<string, [number, number, string, string]> = { "upper left": [0.02, 0.03, "left", "top"], "upper right": [0.98, 0.03, "right", "top"],
        "lower left": [0.02, 0.97, "left", "bottom"], "lower right": [0.98, 0.97, "right", "bottom"],
        "center": [0.5, 0.5, "center", "middle"] };
      const pos = (Object.hasOwn(POS, a.where!) ? POS[a.where!] : undefined) ?? [0.98, 0.03, "right", "top"];
      t(A.x0 + pos[0] * (A.x1 - A.x0), A.y0 + pos[1] * (A.y1 - A.y0), a, pos[2], pos[3], a.color);
    }
  }
  return els;
}
