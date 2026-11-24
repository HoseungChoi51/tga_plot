// The live (browser) version of a resolved curve figure: the same option as the static render, but every label is
// tied to the data (markPoint / markLine on its series), so it moves with zoom, pan and resize, plus a tooltip and
// zoom. The static render places labels in pixels to avoid collisions; a live chart cannot. A port of
// plotkit/js/live.mjs (as Python's plotkit, the live option does not merge the spec's "echarts" patch).
import { buildOption, layout } from "./translate.ts";
import type { Figure } from "./curves.ts";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Option = Record<string, any>;

/** One figure's live ECharts option, as live.mjs builds it (the axis tick formatters are functions). */
export function liveOption(fig: Figure): Option {
  const L = layout(fig);
  const o = buildOption(fig, L);
  const seriesFor = (axis: string, sheet?: string) => o.series.findIndex((s: Option, i: number) => i < fig.series.length && fig.series[i].axis === axis &&
    (sheet === undefined || fig.series[i].sheet === sheet));
  const add = (idx: number, item: Option) => {
    if (idx < 0) return;
    const s = o.series[idx];
    s.markPoint = s.markPoint ?? { silent: false, animation: false, data: [] };
    s.markPoint.data.push(item);
  };
  for (const a of fig.annotations) {
    if (a.kind === "value" || a.kind === "peak" || a.kind === "text_at") {
      const idx = seriesFor(a.axis ?? "y1");
      add(idx < 0 ? 0 : idx, {
        coord: [a.x, a.y], value: a.text, symbol: a.kind === "peak" ? "triangle" : "circle", symbolSize: 7,
        symbolRotate: a.kind === "peak" && a.down ? 180 : 0,
        itemStyle: { color: a.kind === "value" ? "#ffffff" : a.color, borderColor: a.color, borderWidth: 1.5 },
        label: { show: true, formatter: a.text, position: a.kind === "peak" && a.down ? "bottom" : "top", distance: 6,
          color: a.text_color ?? a.color, fontSize: a.size * 96 / 72, fontFamily: fig.font_family,
          backgroundColor: "rgba(255,255,255,0.85)", padding: [1, 3] },
      });
    }
  }
  for (const s of o.series) if (s.markLine?.data) for (const d of s.markLine.data) d.label = { show: false };
  for (const a of fig.annotations) {
    if ((a.kind === "vline" || a.kind === "hline") && a.text) {
      const s = o.series.find((x: Option) => String(x.name).startsWith("__marks_"));
      const d = s?.markLine?.data?.find((x: Option) => (a.kind === "vline" ? x.xAxis : x.yAxis) === a.value);
      if (d) d.label = { show: true, formatter: a.text, position: "insideEndTop", color: a.text_color, fontSize: a.size * 96 / 72 };
    }
  }
  o.tooltip = { trigger: "axis", confine: true };
  o.dataZoom = [{ type: "inside", xAxisIndex: L.split ? [0, 1] : 0, filterMode: "none" }];
  o.animation = false;
  return o;
}

/** The live options of resolved figures, as plain JSON: what live.mjs printed and Python's
 *  plotkit.echarts_options returns (no functions; undefined keys dropped). */
export function liveOptions(figures: Figure[]): Option[] {
  return JSON.parse(JSON.stringify(figures.map(liveOption)));
}
