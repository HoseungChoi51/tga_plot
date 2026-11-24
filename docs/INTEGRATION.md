# Integrating plotkit into an app

For the developer of a chat app (KetchupE, Electron) that wants plots from a language model. plotkit is a Python
library with a small Node part. The app keeps the conversation and calls the model; plotkit writes the prompt, reads
the data, checks the model's spec and turns it into ECharts options or files. How the front end looks is yours to
design. This page is the recommended way to wire it.

## The recommended configuration

| choice | setting | why (see [EXPERIMENTS.md](EXPERIMENTS.md)) |
|---|---|---|
| what the model writes | a JSON spec, never plotting code | 93–94% of keyed asks right at ~50 output tokens; raw code was slower and less reliable |
| engine | ECharts, live in the renderer; files from the same spec | one engine for the view and the export |
| reasoning | off; a "think harder" toggle turns it on for one request | +13–16 points overall on the spec path, but slower on every request, and a no-key ask can trap it |
| constrained decoding | none | free decoding plus plotkit's error + hint is already at 95–98% |
| retries | at most 2, with plotkit's error and hint, hidden from the user | as in every study run |

## Install

```
pip install -e .                       # numpy, pandas, matplotlib, scipy, openpyxl (+ [xls] for .xls files)
npm install --prefix plotkit/js        # echarts (live options, SVG), sharp (PNG/JPG/TIF), playwright-core (PDF)
npx --prefix plotkit/js playwright install chromium     # only for PDF; or set PLOTKIT_CHROMIUM
```

matplotlib is needed even with ECharts (colour parsing, tick choice). Node 20 or newer.

## One request, step by step

```
user: request + attached files
  │
  ├─ messages = [system_prompt(), first_message(request, files, base)]      ← preview of the data, then the request
  ├─ reply = <your model>(messages, **request_options(reasoning=toggle))
  ├─ spec = parse_reply(reply)
  ├─ result = echarts_options(spec, base, full=True)
  │     ok    → show result["options"] (revive, then setOption); tell the user result["not_done"]
  │     PlotkitError e → messages += [reply, retry_message(e)]; ask the model again (at most twice)
  │
follow-up on the same plot ("make the bars horizontal"):
  └─ messages += [followup_message(request)]  (the history holds the last spec) → same loop
```

`plotkit.agent.run()` is this loop with your model as a callable; read it, use it, or copy it:

```python
import plotkit

def llm(messages, **options):          # your model call; options = request_options(...)
    return my_client.chat(model=..., messages=messages, extra_body=options)

r = plotkit.agent.run("반응기별 평균 수율, R3만", ["run_log.xlsx"], llm, base="/path/to/attachments")
if r["ok"]:
    send_to_renderer(r["options"])      # list of ECharts options, one per figure
    if r["not_done"]:
        say("못 한 것: " + ", ".join(r["not_done"]))
later = plotkit.agent.run("가로 막대로", ["run_log.xlsx"], llm, base=..., history=r["transcript"])
```

### Where the preview comes from

The model never reads the files. `plotkit.preview(files, base)` reads them (Excel sheets, CSV/TXT with any
separator, decimal commas, units rows, metadata on top, Korean headers, cp949/UTF-16) and writes what the model
needs, in Korean: per sheet the row count and every column with its letter, type and range or values. That text and
the user's request make the first message (`first_message`). Show the user the files; send the model the preview.

### Errors and hints

Every problem comes back as `plotkit.PlotkitError(message, hint)`: an unknown key (with "did you mean"), a sheet
or column that does not exist (with the real ones), a bad value, a reply with no JSON. `retry_message(e)` turns it
into the next user turn. Keep these turns out of the visible chat: the user sees the final plot, or, after two failed
retries, a short "could not draw it" with `error`.

### The reasoning toggle

`request_options(reasoning, provider, model)` returns the fields to merge into the request:

| provider | off (default) | on |
|---|---|---|
| `openai-compatible` (llama.cpp, vLLM, SGLang; Qwen-style templates) | `chat_template_kwargs.enable_thinking: false` | `true` |
| `anthropic` (Messages API) | thinking off where the model allows it (`disabled`, or `between_tools` on Claude Sonnet 5.5), effort `low`; Claude Opus 5.5 and Fable cannot switch thinking off, so only effort `low` | adaptive thinking, effort `high` |

Pass `model` for Anthropic; without it the fields are the ones every current model accepts. A `/no_think` text in
the prompt does not switch Qwen's thinking off; the template flag does.

### Live view and export

- **Live:** `echarts_options(spec, base)` returns one ECharts option per figure, built without writing files. Labels
  are tied to the data, so they stay put under zoom and resize; tooltip and zoom are on. Chart options can hold
  markers for functions (`"__fmt__{:.1f}"`, `"__histbar__"`, `"__errorbar__"`). In the renderer:

  ```js
  import { revive } from "plotkit/js/revive.mjs";     // no imports, no Node APIs
  chart.setOption(revive(option));
  ```

  Curve options are built in Node (`plotkit/js/live.mjs`), so the sidecar needs Node; chart options are pure Python.
- **Export:** `render(spec, out_dir, formats=("png", "pdf"), engine="echarts")` writes the files and returns their
  paths in `saved`. The app chooses the folder and formats; the spec's own `output` is overridden. PNG/JPG/TIF need
  sharp, PDF needs Chromium. `summary_csv=True` also writes the residue and peak values of curves.

Both return the same result shape for curves and charts: `ok`, `kind` (`curve` | `chart`), `engine`, `options` or
`saved`, `warnings`, `not_done`, `values` (the numbers plotted: residue and peaks per sheet, bar heights, ...).

## Calling Python from Electron

**Now: a sidecar.** Start `python -m plotkit serve` once and talk JSON lines over stdin/stdout:

```js
import { spawn } from "node:child_process";
import readline from "node:readline";

const py = spawn("python", ["-m", "plotkit", "serve"], { cwd: PLOTKIT_DIR });
const pending = new Map();
readline.createInterface({ input: py.stdout }).on("line", line => {
  const msg = JSON.parse(line);
  pending.get(msg.id)?.(msg);
  pending.delete(msg.id);
});
let nextId = 1;
function call(method, params) {
  const id = nextId++;
  py.stdin.write(JSON.stringify({ id, method, params }) + "\n");
  return new Promise(resolve => pending.set(id, resolve));
}

const prompt = (await call("prompt", {})).result;
const first = (await call("first_message", { request, files, base })).result;
// ... call your model with [system: prompt, user: first] ...
const res = await call("options", { spec, base });   // res.ok ? res.result.options : retry with res.error / res.hint
```

Methods: `prompt`, `preview`, `first_message`, `followup_message`, `parse_reply`, `retry_message`,
`request_options`, `validate`, `options`, `render`, `schema`. Requests are answered one at a time, in order; a
failed request answers `{"id", "ok": false, "error", "hint"}` and the sidecar keeps running.

**Later: TypeScript.** The ECharts side already is JavaScript: `plotkit/js/translate.mjs` (curve figure → option,
label layout) imports nothing and can run in the renderer. Porting the rest means porting the reader and the
resolver (`plotkit/core.py`, `plotkit/echarts.py`, `plotkit/charts.py`); the schema below and the reference specs
in `tests/` are the contract to test a port against.

## The spec schema

- `schema/plotkit.spec.schema.json`: a JSON Schema (2020-12) of the spec, independent of any data file (file, sheet
  and column names are strings). Generate TypeScript types from it, e.g. with json-schema-to-typescript.
- `schema/SPEC.md`: every key with its type, default, aliases and meaning.

Both are generated from the tables plotkit's checks use, and a test keeps them in step. The schema describes the
canonical spec; plotkit also accepts aliases (`"y축"` for `y1`, `"점선"` for `dotted`, ...), listed in the schema
under `x-plotkit-aliases` and `x-plotkit-value-aliases`. So check what the model wrote with `plotkit.validate()`
(or `options`), not with the schema: plotkit maps the aliases and answers mistakes with a hint the model can use.
Use the schema for specs the app writes or edits itself.

## Sandbox and escape hatches

Three keys run or carry code the model wrote:

| key | what it is | where it runs |
|---|---|---|
| `data_code` | Python on the data before drawing (`df`, or `x`/`y1`/`y2`), both engines | a separate Python process in bubblewrap: no network, read-only system, private `/tmp`; results come back as JSON and `.npy`, never pickle |
| `echarts` | a partial ECharts option merged over the plot | not code: checked against an allowlist; functions, URLs and data URLs are refused |
| `code` | matplotlib lines after drawing | **in the app's Python process** (`exec`); the ECharts engine refuses it |

On Windows and macOS there is no bubblewrap, so `data_code` is **refused** with an error and a hint the model acts
on (it draws with keys only, or reports the ask as not done). The app can allow plain-subprocess runs with
`allow_unsandboxed=True` on the call, `plotkit.sandbox.allow_unsandboxed(True)`, or `PLOTKIT_ALLOW_UNSANDBOXED=1`; the
code then runs with the user's rights. With the recommended ECharts configuration the model is never shown `code`,
and the engine refuses it; do not use `render(..., engine="matplotlib")` on specs from a model unless you accept
`code` running in-process.

## Known gaps

- Asks with no key fail quietly: the model writes the nearest key and plotkit accepts it. The spec's `asks` list
  (returned as `not_done`) is the only signal; show it to the user.
- No keys yet for percent-stacked bars (`percent` is accepted and ignored), box plots, colour rules, unit conversion
  and computed curves (onset, mass loss, DTG from weight).
- ECharts vs matplotlib: line-style aliases (`"--"`, `"점선"`) draw solid on ECharts; a residue label beyond `x.max`
  is drawn outside the plot on ECharts; automatic ticks differ on small or large-font figures; `inout` ticks are
  approximated.
- Paths in a spec are file names; resolve them against the folder you pass as `base` (the attachments folder).
