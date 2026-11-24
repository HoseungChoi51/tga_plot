#!/usr/bin/env node
// The live (browser) version of a resolved curve plot: the same option as the static render, but every label is
// tied to the data (markPoint / markLine on its series), so it moves with zoom, pan and resize, plus a tooltip,
// zoom and a toolbox. The static render places labels in pixels to avoid collisions; a live chart cannot.
//
//   node plotkit/js/live.mjs < resolved.json     (input: {"figures": [...]} from plotkit.echarts.resolve)
// Prints {"ok": true, "options": [...]}.
import { buildOption, layout } from "./translate.mjs";

export function liveOption(fig) {
  const L = layout(fig);
  const o = buildOption(fig, L);
  const seriesFor = (axis, sheet) => o.series.findIndex((s, i) => i < fig.series.length && fig.series[i].axis === axis &&
    (sheet === undefined || fig.series[i].sheet === sheet));
  const add = (idx, item) => {
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
      const s = o.series.find(x => String(x.name).startsWith("__marks_"));
      const d = s?.markLine?.data?.find(x => (a.kind === "vline" ? x.xAxis : x.yAxis) === a.value);
      if (d) d.label = { show: true, formatter: a.text, position: "insideEndTop", color: a.text_color, fontSize: a.size * 96 / 72 };
    }
  }
  o.tooltip = { trigger: "axis", confine: true };
  o.dataZoom = [{ type: "inside", xAxisIndex: L.split ? [0, 1] : 0, filterMode: "none" }];
  o.animation = false;
  return o;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  try {
    process.stdout.write(JSON.stringify({ ok: true, options: input.figures.map(liveOption) }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(e?.message ?? e) }) + "\n");
    process.exitCode = 1;
  }
}
