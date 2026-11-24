# plotkit/js

The Node side of the ECharts engine (`PLOTKIT_ENGINE=echarts`, or `python -m plotkit plot ... --engine echarts`).

- `plotkit/echarts.py` resolves a curve spec into plain numbers, colours, texts and tick
  positions, and checks the `"echarts"` patch against an allowlist.
- `translate.mjs` turns that into an ECharts option and lays out the residue and peak labels
  (a port of `plotkit.core._place_labels`). It imports nothing, so it can run in the Electron
  renderer as it is.
- `live.mjs` reads `{"figures": [...]}` on stdin and prints the live options (no files).
- `render.mjs` reads `{"figures": [...]}` on stdin, renders server-side SVG with ECharts, and
  writes SVG, PNG/JPG/TIF (sharp) or PDF (headless Chromium), the same tools KetchupE uses.
- `render_chart.mjs` does the same for the chart options `plotkit/charts.py` builds, and holds
  `revive()`, which turns the `__fmt__…`, `__histbar__` and `__errorbar__` markers back into functions.
- `dump.mjs` writes what was drawn (`PLOTKIT_DUMP_OPTION=<file>`), for the experiments' checker.

Install: `npm install --prefix plotkit/js` (Node.js 20+). PDF also needs a Chromium: run
`npx --prefix plotkit/js playwright install chromium`, or set `PLOTKIT_CHROMIUM` to a Chrome/Chromium
path (on Windows, Edge is found automatically).

The versions of `echarts` (6.1.0) and `sharp` (^0.35) match KetchupE's `package.json`.
