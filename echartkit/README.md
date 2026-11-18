# echartkit

The ECharts engine behind `PLOTKIT_ENGINE=echarts` (or `plotkit.py plot ... --engine echarts`).

- `plotkit_echarts.py` (repo root) resolves a spec into plain numbers, colours, texts and tick
  positions, and checks the `"echarts"` patch against an allowlist.
- `translate.mjs` turns that into an ECharts option and lays out the residue and peak labels
  (a port of `plotkit._place_labels`). This is the part that would move into KetchupE's
  `electron/excel/chart.ts`.
- `render.mjs` reads `{"figures": [...]}` on stdin, renders server-side SVG with ECharts, and
  writes SVG, PNG/JPG/TIF (sharp) or PDF (headless Chromium), the same tools KetchupE uses.

Install: `npm install` in this folder (Node.js 20+). PDF also needs a Chromium: run
`npx playwright install chromium`, or set `PLOTKIT_CHROMIUM` to a Chrome/Chromium path
(on Windows, Edge is found automatically).

The versions of `echarts` (6.1.0) and `sharp` (^0.35) match KetchupE's `package.json`.
