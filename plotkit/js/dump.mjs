// What an ECharts chart actually drew, as plain JSON: the final option plus the numbers ECharts
// worked out itself (axis extents and ticks, grid rectangles, the legend box, graphic texts in data
// coordinates). Used only when PLOTKIT_DUMP_OPTION=<file> is set (tests and evaluations).

function axisInfo(model, kind) {
  const out = [];
  for (let i = 0; ; i++) {
    const m = model.getComponent(kind, i);
    if (!m) break;
    const info = { index: i, grid: m.get("gridIndex") ?? 0, type: m.get("type"), position: m.get("position") ?? null };
    try { info.extent = m.axis.scale.getExtent(); } catch { info.extent = null; }
    try { info.ticks = m.axis.scale.getTicks().map(t => (t && typeof t === "object" ? t.value : t)); } catch { info.ticks = null; }
    try { info.minor = m.axis.scale.getMinorTicks ? m.axis.scale.getMinorTicks(m.get("minorTick.splitNumber") ?? 5).flat().length : 0; } catch { info.minor = 0; }
    out.push(info);
  }
  return out;
}

export function chartFacts(chart) {
  const option = chart.getOption();
  const model = chart.getModel();
  const grids = [];
  for (let i = 0; ; i++) {
    const g = model.getComponent("grid", i);
    if (!g) break;
    try { const r = g.coordinateSystem.getRect(); grids.push({ x: r.x, y: r.y, width: r.width, height: r.height }); } catch { grids.push(null); }
  }
  const legends = [];
  for (let i = 0; ; i++) {
    const lm = model.getComponent("legend", i);
    if (!lm) break;
    try {
      const v = chart.getViewOfComponentModel(lm);
      const r = v.group.getBoundingRect();
      legends.push({ x: r.x + v.group.x, y: r.y + v.group.y, width: r.width, height: r.height });
    } catch { legends.push(null); }
  }
  const xAxes = axisInfo(model, "xAxis"), yAxes = axisInfo(model, "yAxis");
  const fromPixel = (gridIndex, px) => {
    const xi = xAxes.findIndex(a => a.grid === gridIndex);
    const ys = yAxes.filter(a => a.grid === gridIndex).map(a => a.index);
    return ys.map(yi => { try { return chart.convertFromPixel({ xAxisIndex: Math.max(0, xi), yAxisIndex: yi }, px); } catch { return null; } });
  };
  const texts = [];
  const walk = (els, ox, oy) => {
    for (const e of els ?? []) {
      if (!e) continue;
      const x = (e.x ?? 0) + ox, y = (e.y ?? 0) + oy;
      if (e.type === "text" && e.style && e.style.text != null && String(e.style.text).trim()) {
        const g = grids.findIndex(r => r && x >= r.x - 2 && x <= r.x + r.width + 2 && y >= r.y - 2 && y <= r.y + r.height + 2);
        texts.push({ text: String(e.style.text), px: [x, y], fill: e.style.fill ?? null, fontSize: e.style.fontSize ?? null,
          grid: g, data: fromPixel(g < 0 ? 0 : g, [x, y]) });
      }
      if (e.children) walk(e.children, x, y);
    }
  };
  for (const g of option.graphic ?? []) walk(g.elements ?? [g], 0, 0);
  return { option, grids, legends, xAxes, yAxes, texts };
}
