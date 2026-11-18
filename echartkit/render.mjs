#!/usr/bin/env node
// echartkit: draws plotkit's resolved plots with ECharts (server-side SVG, as KetchupE does)
// and writes SVG, PNG/JPG/TIF (sharp, as KetchupE's captureChartPng) or PDF (headless
// Chromium, as KetchupE's printToPDF).
//
//   python plotkit.py plot spec.json --engine echarts      (normal use, via plotkit)
//   node echartkit/render.mjs < resolved.json               (input: {"figures": [...]})
//
// Prints one line of JSON: {"ok": true, "figures": [{"saved": [...], "warnings": [...]}]}
// or {"ok": false, "error": "...", "hint": "..."}.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import * as echarts from "echarts";
import { buildOption, layout, mergePatch, placeLabels, lineTexts, legendOption, bestPlace } from "./translate.mjs";

function readStdin() {
  return new Promise((resolve, reject) => {
    const chunks = [];
    process.stdin.on("data", c => chunks.push(c));
    process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    process.stdin.on("error", reject);
  });
}

/** One resolved figure -> SVG text and warnings. */
export function renderSvg(fig) {
  const warnings = [];
  const L = layout(fig);
  if (fig.tick_direction === "inout") warnings.push('tick_direction "inout" has no ECharts setting; drawn as longer outward ticks');
  let option = buildOption(fig, L);
  option = mergePatch(option, fig.echarts, fig);
  const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: L.W, height: L.H });
  try {
    chart.setOption(option);
    const toPixel = a => chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: a.axis === "y2" ? 1 : 0 }, [a.x, a.y]);
    let legendBox = null;
    if (fig.legend.show && !(fig.echarts && fig.echarts.legend)) {
      let where = fig.legend.where;
      if (where === "best") {
        const pts = [];
        for (const s of fig.series) {
          const step = Math.max(1, Math.floor(s.points.length / 400));
          for (let i = 0; i < s.points.length; i += step) pts.push(toPixel({ axis: s.axis, x: s.points[i][0], y: s.points[i][1] }));
        }
        where = bestPlace(fig, L, pts);
        const lg = legendOption(fig, L, where);
        delete lg._box;
        chart.setOption({ legend: lg });
      }
      legendBox = legendOption(fig, L, where)._box;
    }
    const graphics = [
      ...lineTexts(fig, L, toPixel),
      ...placeLabels(fig, L, toPixel, legendBox ? [legendBox] : []),
      ...((fig.echarts && fig.echarts.graphic) || []),
    ];
    if (graphics.length) chart.setOption({ graphic: { elements: graphics } });
    let svg = chart.renderToSVGString();
    // a real size in the file, so other programs (Word, PowerPoint, Inkscape) open it at the asked inches
    svg = svg.replace(/^<svg /, `<svg data-plotkit-dpi="${fig.dpi}" `);
    return { svg, warnings, W: L.W, H: L.H };
  } finally {
    chart.dispose();
  }
}

let browser = null;
async function chromium() {
  if (browser) return browser;
  const { chromium: pw } = await import("playwright-core");
  const tries = [];
  if (process.env.PLOTKIT_CHROMIUM) tries.push({ executablePath: process.env.PLOTKIT_CHROMIUM });
  tries.push({});
  if (process.platform === "win32") tries.push({ channel: "msedge" });
  tries.push({ channel: "chrome" });
  let last;
  for (const opts of tries) {
    try { browser = await pw.launch({ headless: true, ...opts }); return browser; } catch (e) { last = e; }
  }
  throw Object.assign(new Error("PDF output needs Chromium, Chrome or Edge, and none could be started: " + String(last?.message ?? last).split("\n")[0]),
    { hint: "set PLOTKIT_CHROMIUM to the browser's full path, or run: npx --prefix echartkit playwright install chromium" });
}

async function writeOutputs(fig, svg, W, H) {
  const saved = [];
  for (const o of fig.outputs) {
    mkdirSync(dirname(o.path), { recursive: true });
    if (o.format === "svg") {
      writeFileSync(o.path, svg);
    } else if (o.format === "pdf") {
      const b = await chromium();
      const page = await b.newPage();
      try {
        const w = fig.size_in[0], h = fig.size_in[1];
        await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>@page{size:${w}in ${h}in;margin:0}html,body{margin:0;padding:0}svg{display:block}</style></head><body>${svg}</body></html>`);
        writeFileSync(o.path, await page.pdf({ width: `${w}in`, height: `${h}in`, printBackground: true, pageRanges: "1" }));
      } finally { await page.close(); }
    } else {
      const { default: sharp } = await import("sharp");
      // librsvg reads the SVG at 72 dpi; the SVG is laid out at 96 px per inch
      let img = sharp(Buffer.from(svg), { density: 72 * fig.dpi / 96, limitInputPixels: 400_000_000 })
        .resize(Math.round(fig.size_in[0] * fig.dpi), Math.round(fig.size_in[1] * fig.dpi), { fit: "fill" })
        .flatten({ background: "#ffffff" });
      img = o.format === "png" ? img.png() : o.format === "jpg" ? img.jpeg({ quality: 95 }) : img.tiff({ compression: "lzw" });
      img = img.withMetadata({ density: fig.dpi });
      writeFileSync(o.path, await img.toBuffer());
    }
    saved.push(o.path);
  }
  return saved;
}

async function main() {
  const input = JSON.parse(await readStdin());
  const out = [];
  for (const fig of input.figures) {
    const { svg, warnings, W, H } = renderSvg(fig);
    out.push({ saved: await writeOutputs(fig, svg, W, H), warnings });
  }
  return { ok: true, figures: out };
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith("render.mjs")) {
  main().then(r => { process.stdout.write(JSON.stringify(r) + "\n"); },
    e => { process.stdout.write(JSON.stringify({ ok: false, error: String(e.message ?? e), hint: e.hint ?? "" }) + "\n"); process.exitCode = 1; })
    .finally(async () => { if (browser) await browser.close(); });
}
