# plotkit-ts

A language model writes a small JSON **spec**; plotkit-ts checks it against the user's data files and draws it with
ECharts, as SVG for export or as live ECharts options. It is TypeScript and needs no Python: it runs in the app's own
Node/Electron process.

```json
{"file": "run_log.xlsx", "sheets": "런로그", "chart": "bar", "x": "반응기",
 "y": {"col": "CNT수율", "agg": "mean"}, "filter": ["주차 >= 10"],
 "asks": [{"ask": "반응기별 평균 수율", "how": "key"}, {"ask": "10주차부터", "how": "key"}]}
```

Two kinds of plot share the spec: **curves** from instrument exports (x, a left axis y1, a right axis y2; residue and
peak labels for TGA) and **charts** of table data (bar, hbar, line, scatter, histogram, heatmap, pie; filters,
grouping, aggregation, periods, bins).

plotkit-ts is a port of the Python plotkit (branch `lib/plotkit` of this repository), which stays the reference and
holds the studies behind the design. The tests here check the port against that implementation case by case.

## Install

```
npm install "git+https://github.com/HoseungChoi51/tga_plot.git#lib/plotkit-ts"
```

npm builds `dist/` (ESM JavaScript and `.d.ts`) on install (`prepare`). Peer dependencies: `echarts` 6.1.0,
`exceljs` ^4.4 (reading .xlsx, loaded on first use), and optionally `quickjs-emscripten` 0.32 (the built-in data_code
sandbox, loaded only by `quickjsRunCode`). Node 22.6+ or any bundler; no native code, no child processes.

## Use

```ts
import { systemPrompt, firstMessage, parseReply, retryMessage, requestOptions, renderSvg, PlotkitError }
  from "plotkit-ts";

const files = [{ name: "run_log.xlsx", bytes }];            // the user's files as {name, bytes}
const messages = [{ role: "system", content: systemPrompt() },
                  { role: "user", content: await firstMessage("반응기별 평균 수율", ["run_log.xlsx"], files) }];
for (let attempt = 0; attempt < 3; attempt++) {
  const reply = await callModel(messages, requestOptions());           // thinking off by default
  messages.push({ role: "assistant", content: reply });
  try {
    const out = await renderSvg(parseReply(reply), files, { runCode });
    // out.files: [{name, svg, width, height, size_in, dpi}] -> PNG/PDF by the app
    // out.not_done: the asks the model marked unsupported (tell the user); out.values: the numbers drawn
    break;
  } catch (e) {
    if (!(e instanceof PlotkitError)) throw e;
    messages.push({ role: "user", content: retryMessage(e) });        // error + hint back to the model, hidden from the user
  }
}
```

`run(request, names, files, llm)` is that loop with the model as a function. `echartsOptions(spec, files)` returns live
options instead (labels tied to the data, tooltip, zoom; call `revive(option)` before `setOption`).

| function | what it does |
|---|---|
| `systemPrompt()` | the model's instructions (the spec, the asks, examples, the ECharts hatch) |
| `firstMessage(request, names, files)`, `followupMessage(request)` | the user turns; the first holds the data preview |
| `previewText(names, files)` | what the model sees of the data: sheets, rows, every column with letter, type and values |
| `parseReply(text)`, `retryMessage(err)` | the spec in a reply; the turn that sends an error and its hint back |
| `requestOptions(reasoning)` | `chat_template_kwargs.enable_thinking` for a locally served model |
| `validate(spec, files, opts)` | check without drawing: the normalized spec, warnings, not_done |
| `renderSvg(spec, files, opts)` | SVG per figure, values, warnings, not_done |
| `echartsOptions(spec, files, opts)` | live ECharts options, values, warnings, not_done |
| `run(request, names, files, llm, opts)` | the reference loop: preview → model → parse → options, at most 2 retries |
| `quickjsRunCode()` | a sandbox for data_code on QuickJS, if the app has none |

Every problem is a `PlotkitError(message, hint)`; send it back with `retryMessage`.

## The data hatch (`data_code`)

The model may transform the data with a few lines of JavaScript (unit change, ratios, labels, an onset). plotkit-ts
never runs that code itself: it builds a function body and calls the app's `runCode(body, input)`, which must run it
in a sandbox and return JSON. Without `runCode`, a spec with data_code is refused with an error and a hint, and the
model draws with keys only. See [docs/INTEGRATION.md](docs/INTEGRATION.md).

## What it does not do

Old binary `.xls` (ExcelJS cannot read them: save as `.xlsx`); the matplotlib engine and its Python `code` hatch
(Python plotkit only); PNG/PDF (the app converts the SVG); colormaps beyond the 30 built in (and their `_r`).

## Tests

`npm test` (offline; runs the `.ts` sources directly with Node's type stripping): 493 tests. The goldens in `test/golden/` were written by the Python plotkit
(`tools/ts_golden.py` on `lib/plotkit`): every data file's tables and preview, 3,985 specs (276 hand-written, 3,709
written by models in the studies) with the normalized spec or the error and hint, and 776 drawn end to end with their
options, values and SVG. `src/tables.ts`, `src/prompts.ts` and `src/data/colors.json` are generated there too
(`tools/ts_tables.py`); do not edit them by hand.

## Layout

`src/`: `api.ts` (validate, echartsOptions, renderSvg, routing), `agent.ts` (prompt, messages, the loop),
`reader.ts` / `frame.ts` / `preview.ts` (files, tables, previews), `spec.ts` / `chartspec.ts` / `patch.ts` (the spec
check), `jobs.ts` / `curves.ts` / `peaks.ts` / `translate.ts` / `live.ts` / `render.ts` (curves), `charts.ts` /
`chartdata.ts` / `chart_render.ts` (charts), `hatch.ts` / `quickjs.ts` (data_code), and Python-exact helpers
(`pyfmt.ts`, `difflib.ts`, `colors.ts`, `ticks.ts`). `prompts/` holds the prompt's source.
