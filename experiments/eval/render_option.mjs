#!/usr/bin/env node
// Renders ECharts options written by a model (raw-ECharts arms) the way plotkit's engine does:
// ECharts SSR SVG, then sharp (PNG/JPG/TIF) or Chromium (PDF) via plotkit/js/render.mjs's writeOutputs.
//
//   node eval/render_option.mjs < {"out_dir": "...", "figures": [{name, option, width, height, dpi, formats}]}
// Prints {"ok": true, "saved": [...]} or {"ok": false, "error": "..."}; with PLOTKIT_DUMP_OPTION=<file>
// also writes what was drawn (plotkit/js/dump.mjs) for the figure-facts checker.
import { writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { chartFacts } from "../../plotkit/js/dump.mjs";
import { writeOutputs, closeBrowser } from "../../plotkit/js/render.mjs";

const require = createRequire(new URL("../../plotkit/js/package.json", import.meta.url));
const echarts = require("echarts");

const chunks = [];
for await (const c of process.stdin) chunks.push(c);
const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
const dump = [];
const saved = [];
try {
  const figs = input.figures ?? [];
  if (!figs.length) throw new Error("no figures in the printed JSON");
  for (const [i, f] of figs.entries()) {
    if (!f || typeof f.option !== "object") throw new Error(`figure ${i}: "option" must be an object`);
    const W = Math.round(Number(f.width) || 640), H = Math.round(Number(f.height) || 460);
    const dpi = Number(f.dpi) || 300;
    const formats = (Array.isArray(f.formats) && f.formats.length ? f.formats : ["png"]).map(s => String(s).toLowerCase().replace("jpeg", "jpg").replace("tiff", "tif"));
    const name = String(f.name || `figure${i + 1}`).replace(/[\\/:*?"<>|\s]+/g, "_");
    const chart = echarts.init(null, null, { renderer: "svg", ssr: true, width: W, height: H });
    try {
      chart.setOption({ animation: false, backgroundColor: "#ffffff", ...f.option });
      const outputs = formats.map(fmt => ({ path: join(input.out_dir, `${name}.${fmt}`), format: fmt }));
      if (process.env.PLOTKIT_DUMP_OPTION) dump.push({ ...chartFacts(chart), W, H, size_in: [W / 96, H / 96], dpi, outputs });
      const svg = chart.renderToSVGString();
      saved.push(...await writeOutputs({ outputs, size_in: [W / 96, H / 96], dpi }, svg, W, H));
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
