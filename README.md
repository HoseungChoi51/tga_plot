# TGA plots for a local AI agent (plotkit)

One tool, `plotkit.py`, draws TGA/DTG plots (or any x–y plot) from Excel or text files.
A local LLM controls it by writing a short JSON **spec**, never by editing code.
Every part of the plot has a Korean name in `guide/guide_ko.png`, and each name maps to
exactly one spec key in `AGENT.md`. Users who use those names get predictable results.

## Files

| file | what it is |
|---|---|
| `plotkit.py` | the plotting tool (inspect, plot, schema, example) |
| `AGENT.md` | system prompt for the local LLM: workflow, rules, part name → key table, examples |
| `guide/guide_ko.png` | the guide image for users (15 numbered parts + other terms) |
| `run_agent.py` | a minimal agent: one request → one model call → plot (retries on errors) |
| `tests/AGENT_TEST_PROMPTS.md` | 24 Korean test requests, ready to paste into an agent that runs commands itself (e.g. pi) |
| `tests/inputs/` | 12 test files in different formats (made by `tests/make_test_inputs.py`) |
| `tests/run_tests.py` | checks the reader on all test files (no LLM) |
| `plotkit_echarts.py`, `echartkit/` | the optional ECharts engine (`PLOTKIT_ENGINE=echarts`); needs Node.js |
| `AGENT_ECHARTS.md` | `AGENT.md` for the ECharts engine (`"echarts"` settings instead of `"code"`) |
| `EXPERIMENT.md` | how to compare the two engines with the same model and the 24 test requests |
| `tests/score.py`, `tests/expected_requests.json` | scores an agent's spec for one test request |
| `examples/` | the plot made from the long example request in the original question |
| `old/` | the first version (`tga_plot_v1.py`) and its sample data |
| `eval/` | the protocol evaluation: six arms (spec vs raw code, both engines), figure-facts checker, parity, coverage, safety |
| `gallery/` | 26 example specs on made-up data, drawn by both engines (`python gallery/make_gallery.py`) |
| `report/` | builds the evaluation report page from `eval/results/` |
| `HANDOFF.md` | state of the evaluation and how to continue it on another machine |

## Install (once)

    pip install numpy matplotlib scipy openpyxl xlrd

Optional ECharts engine (Node.js 20+): `npm install --prefix echartkit`, then add
`--engine echarts` or set `PLOTKIT_ENGINE=echarts`. See `EXPERIMENT.md`.

## Use it by hand

    python plotkit.py inspect TGA.xlsx                 # sheets, columns, which column is what
    python plotkit.py plot TGA.xlsx                    # every sheet with the TGA defaults
    python plotkit.py plot spec.json                   # with your settings
    python plotkit.py plot --json "{\"file\": \"TGA.xlsx\", \"x\": {\"step\": 200}}"

Plots and `summary.csv` (residue and peak values) go to `<file>_plots/` next to the data.

## Use it with the local LLM

**Option A, your agent app** (Open WebUI, Qwen-Agent, LM Studio, ...): paste `AGENT.md` as the
system prompt and give the model a shell or Python tool. It runs `inspect`, writes `spec.json`,
runs `plot`, and reports.

**Option B, `run_agent.py`** (fastest, fewest model calls):

    python run_agent.py --base-url http://localhost:11434/v1 --model <model name> \
        --file TGA.xlsx --request "1006R1-V normal 시트, x축 틱 간격 200, 피크 표시 2개" --no-think

It runs `inspect` itself, makes one model call for the spec, plots, and prints a Korean summary.
If plotkit rejects the spec, the error and hint go back to the model (at most 2 retries).

## What makes it reliable

- The model fills in 5–15 lines of JSON instead of writing code. Defaults cover the rest.
- `inspect` gives the model the real sheet names and column letters, so it never guesses.
- plotkit checks every key. Unknown keys and bad values come back as `error` + `hint`
  (e.g. `unknown key "y1.tick_spacing"` is mapped to `step`; a missing sheet lists the real ones).
- Common alternative key names are accepted (`tick_interval` → `step`, `y축` → `y1`, Korean colors).
- Anything with no key can still be done with a few matplotlib lines in `"code"`.
- The reader handles blank and metadata rows on top, units rows, extra or reordered columns,
  Korean or unusual headers, files with no headers (guessed from the values), CSV/TXT with tab,
  comma, semicolon or space separators, decimal commas, UTF-16 instrument exports, cp949 Korean CSVs, and old .xls.
- Korean text uses Malgun Gothic (Windows), AppleGothic (Mac) or Nanum Gothic (Linux) automatically.
