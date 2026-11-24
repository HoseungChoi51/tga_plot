# plotkit-ts

The TypeScript build of plotkit: a language model writes a small JSON spec, plotkit-ts checks it against the user's
data and turns it into ECharts options and SVG. No Python: it runs in the app's own Node/Electron process. It is a
port of the Python package in `../plotkit`, tested against it case by case (`test/`, goldens from
`../tools/ts_golden.py`).

## Install

```
npm install ./ts          # peer dependencies: echarts 6.1.0, exceljs ^4.4 (optional: quickjs-emscripten 0.32)
```

ESM TypeScript with `.ts` imports, as the app's own sources; Vite bundles it. Node 22.6+ runs it directly.

## Use

```ts
import { systemPrompt, firstMessage, parseReply, retryMessage, requestOptions, echartsOptions, renderSvg }
  from "plotkit-ts";

const files = [{ name: "run_log.xlsx", bytes }];                 // what the user attached, as {name, bytes}
const messages = [{ role: "system", content: systemPrompt() },
                  { role: "user", content: await firstMessage("반응기별 평균 수율", ["run_log.xlsx"], files) }];
const reply = await callModel(messages, requestOptions());      // thinking off by default
try {
  const spec = parseReply(reply);
  const out = await renderSvg(spec, files, { runCode });       // SVG per figure; PNG/PDF: the app's sharp/printToPDF
  // out.svgs, out.values, out.not_done (asks the model marked unsupported: tell the user)
} catch (e) {
  messages.push({ role: "assistant", content: reply }, { role: "user", content: retryMessage(e) });   // ≤ 2 retries
}
```

`agent.run(request, names, files, llm)` is that loop with the model as a function. `echartsOptions(spec, files)`
returns live options instead of SVG (labels tied to the data, tooltip, zoom; call `revive(option)` before
`setOption`).

## The data hatch (`data_code`)

The model can transform the data with a few lines of JavaScript (unit change, ratios, labels, onset). plotkit-ts
never runs that code itself: it builds a function body and calls the host's `runCode(body, input)`, which must run
it in a sandbox and return JSON. In KetchupE that is the QuickJS runner of `electron/excel/sandbox.ts`;
`quickjsRunCode()` (this package, needs `quickjs-emscripten`) is the same isolation for hosts without one. Without a
`runCode`, a spec with `data_code` is refused with an error and a hint, and the model draws with keys only.

## What it does not do

Old binary `.xls` (ExcelJS cannot read them: save as `.xlsx`), the matplotlib engine and its `code` hatch (Python
only), PNG/PDF (the app converts the SVG), colormaps beyond the 30 built in.
