#!/usr/bin/env node
// The live (browser) version of a resolved curve plot: the same option as the static render, but every label is
// tied to the data (markPoint / markLine on its series), so it moves with zoom, pan and resize, plus a tooltip,
// zoom and a toolbox. The static render places labels in pixels to avoid collisions; a live chart cannot. The
// model's "echarts" patch is merged last, as in the static render (its graphic elements included).
//
//   node plotkit/js/live.mjs < resolved.json     (input: {"figures": [...]} from plotkit.echarts.resolve)
// Prints {"ok": true, "options": [...]}, or {"ok": false, "error", "hint"} (hint: a problem with the spec's patch).
import { buildOption, layout, mergePatch, withPatchNames } from "./translate.mjs";

export function liveOption(figure) {
  const fig = withPatchNames(figure);       // series renamed in the "echarts" patch: the legend follows
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
  // each line's text on its own line: buildOption puts vlines on y1's helper series and hlines on their axis's, in
  // the order of the annotations
  const next = { y1: 0, y2: 0 };
  for (const a of fig.annotations) {
    if (a.kind !== "vline" && a.kind !== "hline") continue;
    const axis = a.kind === "vline" ? "y1" : a.axis;
    const s = o.series.find(x => x.name === `__marks_${axis}`);
    const d = s?.markLine?.data?.[next[axis]++];
    if (d && a.text) d.label = { show: true, formatter: a.text, position: "insideEndTop", color: a.text_color, fontSize: a.size * 96 / 72 };
  }
  o.tooltip = { trigger: "axis", confine: true };
  o.dataZoom = [{ type: "inside", xAxisIndex: L.split ? [0, 1] : 0, filterMode: "none" }];
  o.animation = false;
  const out = mergePatch(o, fig.echarts, fig);
  const graphic = fig.echarts && fig.echarts.graphic;
  if (Array.isArray(graphic) && graphic.length) out.graphic = { elements: structuredClone(graphic) };
  return out;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  try {
    process.stdout.write(JSON.stringify({ ok: true, options: input.figures.map(liveOption) }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(e?.message ?? e), hint: e?.hint }) + "\n");
    process.exitCode = 1;
  }
}
