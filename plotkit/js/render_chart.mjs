#!/usr/bin/env node
// Renders the ECharts options plotkit/charts.py builds (bar, line, scatter, histogram, heatmap, pie):
// ECharts SSR SVG, then sharp (PNG/JPG/TIF) or Chromium (PDF) via render.mjs's writeOutputs.
// JSON cannot carry functions, so plotkit/charts.py marks them with strings; revive.mjs turns them into functions:
//   "__fmt__{:.1f}"      a value formatter in Python's format mini-language (labels, axis ticks)
//   "__histbar__"        renderItem for a histogram bar: data [x0, x1, count, base]
//   "__errorbar__"       renderItem for an error bar: data [category index, low, high]
//
//   node plotkit/js/render_chart.mjs < {"out_dir": "...", "figures": [{name, option, width, height, dpi, formats}]}
// Prints {"ok": true, "saved": [...]} or {"ok": false, "error": "..."}; with PLOTKIT_DUMP_OPTION=<file>
// also writes what was drawn (dump.mjs) for the figure-facts checker.
import { writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { chartFacts } from "./dump.mjs";
import { writeOutputs, closeBrowser } from "./render.mjs";
import { formatPy, revive } from "./revive.mjs";

export { formatPy, revive };

const require = createRequire(import.meta.url);
const echarts = require("echarts");

async function main() {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const dump = [];
  const saved = [];
  try {
    for (const [i, f] of (input.figures ?? []).entries()) {
      const W = Math.round(Number(f.width) || 640), H = Math.round(Number(f.height) || 460);
      const dpi = Number(f.dpi) || 300;
      const formats = (f.formats?.length ? f.formats : ["png"]).map(s => String(s).toLowerCase());
      const name = String(f.name || `figure${i + 1}`);
      const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: W, height: H });
      try {
        chart.setOption(revive(f.option));
        const outputs = formats.map(fmt => ({ path: join(input.out_dir, `${name}.${fmt}`), format: fmt }));
        const size_in = Array.isArray(f.size_in) ? f.size_in : [W / 96, H / 96];    // the asked inches, not the rounded canvas
        if (process.env.PLOTKIT_DUMP_OPTION) dump.push({ ...chartFacts(chart), W, H, size_in, dpi, outputs });
        const svg = chart.renderToSVGString();
        saved.push(...await writeOutputs({ outputs, size_in, dpi }, svg, W, H));
      } finally {
        chart.dispose();
      }
    }
    if (process.env.PLOTKIT_DUMP_OPTION) writeFileSync(process.env.PLOTKIT_DUMP_OPTION, JSON.stringify({ figures: dump }));
    process.stdout.write(JSON.stringify({ ok: true, saved }) + "\n");
  } catch (e) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(e?.message ?? e).split("\n")[0] }) + "\n");
    process.exitCode = 1;
  } finally {
    await closeBrowser();
  }
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
