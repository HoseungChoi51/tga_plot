# plotkit

A language model writes a small JSON **spec**; plotkit checks it against the user's data and draws it with
**ECharts**, as live options for a chat app or as PNG/SVG/PDF files. matplotlib is an optional second engine. The model never writes plotting code. It fills in the
handful of keys the user asked for, and plotkit supplies the rest: house defaults (a TGA preset), a reader for messy
lab files, and an error with a hint whenever the spec does not fit the data.

```json
{"file": "run_log.xlsx", "sheets": "런로그", "chart": "bar", "x": "반응기",
 "y": {"col": "CNT수율", "agg": "mean"}, "filter": ["주차 >= 10"],
 "asks": [{"ask": "반응기별 평균 수율", "how": "key"}, {"ask": "10주차부터", "how": "key"}]}
```

Two kinds of plot share the spec: **curves** from instrument exports (x, a left axis y1, a right axis y2; residue
and peak labels for TGA) and **charts** of table data (bar, hbar, line, scatter, histogram, heatmap, pie; filters,
grouping, aggregation).

The design comes from a study of about 6,800 scored runs: see [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md).

**For an app, use plotkit-ts** (branch `lib/plotkit-ts`): the default build, TypeScript with no Python. It has the same
spec, prompt, checks, errors and ECharts output, and `data_code` runs as JavaScript in the app's sandbox. This branch
is the Python plotkit: the reference the TypeScript build is tested against, the optional matplotlib engine, and the
studies.

## Install

```
pip install -e .                       # Python 3.10+ (tested on 3.13): numpy, pandas, scipy, openpyxl
pip install -e ".[xls]"                # also old .xls files
pip install -e ".[matplotlib]"         # optional: the matplotlib engine (not needed for ECharts)
npm install --prefix plotkit/js        # Node 20+: ECharts (live options, SVG), sharp (PNG/JPG/TIF)
npx --prefix plotkit/js playwright install chromium     # only for PDF from ECharts
```

## Use it

```python
import plotkit

system = plotkit.system_prompt()                                   # the model's instructions
user = plotkit.first_message("반응기별 평균 수율", ["run_log.xlsx"], base="attachments/")
reply = my_model([{"role": "system", "content": system}, {"role": "user", "content": user}],
                 **plotkit.request_options())                      # thinking off by default
try:
    spec = plotkit.parse_reply(reply)
    options = plotkit.echarts_options(spec, base="attachments/")   # live charts, one option per figure
    plotkit.render(spec, "exports/", formats=("png", "pdf"), base="attachments/")   # or files
except plotkit.PlotkitError as e:
    next_turn = plotkit.retry_message(e)                           # error + hint back to the model, at most twice
```

`plotkit.agent.run(request, files, llm)` does the whole loop with your model as a function. From Electron, run
`python -m plotkit serve` as a sidecar and send it JSON lines. [docs/INTEGRATION.md](docs/INTEGRATION.md) explains
the message flow, the reasoning toggle, live view vs export, the sandbox and the known gaps.

From the shell:

```
python -m plotkit prompt                                  # the system prompt
python -m plotkit preview run_log.xlsx                    # what the model sees of the data
python -m plotkit options spec.json                       # live ECharts options
python -m plotkit render spec.json --out exports --format png,pdf
python -m plotkit inspect TGA.xlsx | plot spec.json       # the older command line
```

## The spec

[schema/SPEC.md](schema/SPEC.md) lists every key with its type, default, aliases and meaning;
[schema/plotkit.spec.schema.json](schema/plotkit.spec.schema.json) is the same as a JSON Schema for TypeScript
types. Both are generated (`python -m plotkit schema --md | --json`) and tested against the code.

## Keeping plotkit-ts in step

A change to the checks or the drawing is made here first, then mirrored in plotkit-ts until its tests pass:

```
git worktree add .worktrees/plotkit-ts lib/plotkit-ts   # once (or set PLOTKIT_TS to a checkout)
python tools/ts_tables.py      # key tables, prompt, colour data -> plotkit-ts/src
python tools/ts_golden.py      # what this plotkit does on every test file and spec -> plotkit-ts/test/golden, test/data
cd .worktrees/plotkit-ts && npm test
```

## Layout

| path | what it is |
|---|---|
| `plotkit/` | the library: `core.py` (file reader, curves, the optional matplotlib engine), `charts.py` (table charts), `echarts.py` (the ECharts engine for curves, the patch allowlist), `colors.py` and `ticks.py` (colours, colormaps and tick choice without matplotlib), `sandbox.py`, `schema.py`, `agent.py` (prompt, messages, reference loop), `api.py`, `__main__.py` (command line, `serve`) |
| `plotkit/prompts/` | the system prompt: `core.md` + `hatch_echarts.md` or `hatch_matplotlib.md` |
| `plotkit/js/` | the Node side: `translate.mjs`, `live.mjs`, `render.mjs`, `render_chart.mjs`, `revive.mjs` |
| `schema/` | the generated spec schema and key reference |
| `docs/` | `INTEGRATION.md` for the app developer, `EXPERIMENTS.md` for the evidence |
| `tests/` | library tests (`python -m pytest tests`) and the reader's test files; `python tests/run_tests.py` checks the reader |
| `tools/` | dev tools for plotkit-ts: `ts_tables.py`, `ts_golden.py` (+ `ts_extra.py`, chart cases the studies never reached), `ts_checkout.py` |
| `experiments/` | the studies behind the design, their harness and results ([experiments/README.md](experiments/README.md)) |

Tests make no network or model calls.
