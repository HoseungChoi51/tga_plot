# Integrating plotkit-ts into KetchupE

Written against KetchupE-Client `main` (Electron 39, TypeScript, Vite; ExcelJS, ECharts 6.1.0, sharp, QuickJS).
plotkit-ts adds no runtime and no native code: it is TypeScript that runs where the Excel work already runs.

## Where it runs

In the Excel `utilityProcess` (`electron/excel/workerClient.ts` / `electron/workers/excel.worker.ts`), next to
`chart.ts`: reading the files, checking the spec and server-side ECharts rendering are plain computation. It reads no
paths and makes no network calls; the app calls the model.

## Files

Pass the user's files as `{name, bytes}` (the tool already gets `{bytes, name}`). The spec names files by these names,
patterns included (`"data/*.csv"`). plotkit-ts reads `.xlsx`/`.xlsm` (ExcelJS) and text files (`.csv`, `.txt`, `.tsv`,
`.dat`: separators, decimal commas, UTF-8/UTF-16/cp949 detected). The app accepts only `.xlsx` today
(`electron/work/sources.ts`, the file dialogs): widen it to take the text formats. Old binary `.xls` is refused with
a hint to save it as `.xlsx`. The app's limits (`electron/excel/limits.ts`) apply before plotkit sees the files.

## The model turns

The system prompt is `systemPrompt()`. The first user turn is `firstMessage(request, names, files)` (a Korean data
preview, then the request); later turns on the same plot are `followupMessage(request)` with the chat history kept.
The reply is one JSON spec (`parseReply`). KetchupE already sends `chat_template_kwargs: {enable_thinking: false}`,
which is `requestOptions()`; pass `requestOptions(true)` for a "think harder" toggle.

Errors are `PlotkitError(message, hint)`: an unknown key ("did you mean"), a sheet or column that does not exist (with
the real ones), a bad value, a reply with no JSON. Send `retryMessage(e)` back to the model, at most twice, and keep
these turns out of the visible chat (the same shape as `electron/excel/tool.ts`'s repair loop). After the retries, tell
the user it could not be drawn.

Show the user `not_done`: the asks the model marked unsupported. Asks with no key otherwise fail quietly (the model
uses the nearest key), so this list is the only signal.

## Drawing

`renderSvg(spec, files, {runCode})` returns one SVG per figure with its size in pixels (96 px per inch), inches and
dpi. Convert with the app's own tools: `captureChartPng` (sharp) for PNG, `printReportPdf` for PDF, or inline the SVG in
a report page (static SVG, no script). zrender numbers SVG ids per chart (`zr0-…`), so rename them before inlining
several charts in one HTML document.

For a live chart in the renderer, `echartsOptions(spec, files)` gives the options (tooltip, zoom, labels tied to the
data); call `revive(option)` (from plotkit-ts, no Node APIs) before `setOption`.

## data_code and the QuickJS sandbox

When no key does what the user asked, the model may write `data_code`: JavaScript on the data, before drawing
(charts: `rows`, an array of row objects; curves: `x`, `y1`, `y2` arrays, `marks`, and helpers such as `interp`,
`gradient`, `median`). plotkit-ts builds a function body and calls `runCode(body, input)`; the body reads `input` and
returns JSON. Give it a generic variant of `electron/excel/sandbox.ts`'s `runAnalysis`: the same QuickJS isolation
(no host callbacks, fixed Date, seeded random, interrupt, non-finite numbers refused), with the input passed as the
function's argument and without `validateResult`:

```ts
const runCode: RunCode = (body, input, signal) => runInQuickJS(body, input, { timeoutMs: L.calculationMs, signal });
```

`quickjsRunCode()` in plotkit-ts is that runner already (it follows `runAnalysis`), if you prefer not to write one.
Without `runCode`, a spec with data_code is refused with an error and a hint, and the model draws with keys only.

## Licences

plotkit-ts is MIT. Add it to `THIRD_PARTY_NOTICES.md` with the parts it ports (matplotlib's colour and tick rules, SciPy's
peak finding, CPython's difflib; see this package's THIRD_PARTY_NOTICES.md).

## Known gaps

- No keys yet for percent-stacked bars, box plots (KetchupE's own chart path draws them), colour rules, unit conversion.
- ECharts vs the Python matplotlib engine: a residue label beyond `x.max` is drawn outside the plot; automatic ticks on
  very small figures differ; `inout` ticks are approximated.
