// E4b: do the labels of a live ECharts chart stay on their data when the user zooms and resizes?
//   node eval/live_check.mjs <cases.json> <out.json>
// cases: [{id, kind ("live" | "static"), option}]. For every text the chart draws whose content is a label we know
// the anchor of (markPoint / bar / heatmap labels: their data coordinate), the offset between the text and its anchor
// is measured, then the chart is zoomed to the middle 40 % of x and resized; a label is attached when its offset
// changed by at most 3 px. Labels whose anchor leaves the view are not counted.
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(new URL("../echartkit/package.json", import.meta.url));
const { chromium } = require("playwright-core");
const echartsJs = readFileSync(require.resolve("echarts/dist/echarts.min.js"), "utf8");
const rc = readFileSync(new URL("../echartkit/render_chart.mjs", import.meta.url), "utf8");
const reviveJs = rc.slice(rc.indexOf("export function formatPy"), rc.indexOf("async function main")).replace(/export function /g, "function ");

const [casesPath, outPath] = process.argv.slice(2);
const cases = JSON.parse(readFileSync(casesPath, "utf8"));
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 900, height: 600 } });
await page.setContent(`<html><body style="margin:0"><div id="c" style="width:800px;height:500px"></div>
<script>${echartsJs}</script><script>${reviveJs}</script></body></html>`);
const results = [];
for (const c of cases) {
  const r = await page.evaluate(([opt, kind]) => {
    const el = document.getElementById("c");
    el.style.width = "800px"; el.style.height = "500px";
    const old = echarts.getInstanceByDom(el); if (old) old.dispose();
    const chart = echarts.init(el, null, { renderer: "canvas" });
    chart.setOption(revive(opt));
    const anchors = [];                  // [text, coord, seriesIndex, axis indices]
    (opt.series || []).forEach((s, si) => {
      const xi = s.xAxisIndex ?? 0, yi = s.yAxisIndex ?? 0;
      for (const d of (s.markPoint?.data || [])) if (d.coord && d.label?.formatter) anchors.push([String(d.label.formatter), d.coord, xi, yi]);
      if (s.type === "bar") (s.data || []).forEach((d, k) => {
        const t = d?.label?.formatter; if (typeof t === "string" && t) {
          const cats = (Array.isArray(opt.xAxis) ? opt.xAxis[0] : opt.xAxis).data;
          const horiz = !cats; const v = d.value;
          anchors.push([t, horiz ? [v, k] : [k, v], xi, yi]);
        }
      });
    });
    if (kind === "static") for (const g of (opt.graphic?.[0]?.elements || opt.graphic || [])) {     // static pixel labels
      if (g?.type === "text" && g.style?.text) anchors.push([String(g.style.text), null, 0, 0, [g.x, g.y]]);
    }
    const texts = () => {
      const out = {};
      chart.getZr().storage.getDisplayList(true).forEach(e => {
        const t = e.style?.text ?? e.__text;
        if (t == null) return;
        const r = e.getBoundingRect(); const m = e.transform || [1, 0, 0, 1, 0, 0];
        const x = (r.x + r.width / 2) * m[0] + m[4], y = (r.y + r.height / 2) * m[3] + m[5];
        (out[String(t)] = out[String(t)] || []).push([x, y]);
      });
      return out;
    };
    const measure = () => {
      const tx = texts(); const out = [];
      for (const [t, coord, xi, yi, px0] of anchors) {
        const pts = tx[t]; if (!pts) { out.push(null); continue; }
        let ap = null;
        if (coord) { try { ap = chart.convertToPixel({ xAxisIndex: xi, yAxisIndex: yi }, coord); } catch (e) { ap = null; } }
        else ap = chart.__anchorData?.[t] ?? null;
        if (!ap) { out.push(null); continue; }
        const p = pts.reduce((a, b) => Math.hypot(b[0] - ap[0], b[1] - ap[1]) < Math.hypot(a[0] - ap[0], a[1] - ap[1]) ? b : a);
        out.push([p[0] - ap[0], p[1] - ap[1], ap]);
      }
      return out;
    };
    // static pixel labels: remember the data point under each one, to follow it after the zoom
    chart.__anchorData = {};
    for (const [t, coord, xi, yi, px0] of anchors) if (!coord && px0) {
      try { const d = chart.convertFromPixel({ xAxisIndex: 0, yAxisIndex: 0 }, px0); chart.__anchorData[t] = null; anchors.find(a => a[0] === t)[1] = d; } catch (e) {}
    }
    const before = measure();
    chart.dispatchAction({ type: "dataZoom", start: 55, end: 95 });
    el.style.width = "620px"; el.style.height = "420px"; chart.resize();
    const after = measure();
    const W = 620, H = 420;
    let n = 0, ok = 0; const bad = [];
    before.forEach((b, i) => {
      const a = after[i];
      if (!b || !a) return;
      const [ax, ay] = a[2];
      if (ax < 0 || ax > W || ay < 0 || ay > H) return;       // the anchor left the view
      n++;
      const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (d <= 3) ok++; else bad.push(`${anchors[i][0].slice(0, 30)}: moved ${d.toFixed(0)} px off its point`);
    });
    return { labels: anchors.length, in_view: n, attached: ok, bad: bad.slice(0, 5) };
  }, [c.option, c.kind]);
  results.push({ id: c.id, kind: c.kind, ...r });
  console.log(c.id, c.kind, JSON.stringify(r));
}
await b.close();
writeFileSync(outPath, JSON.stringify(results, null, 1));
