> Handoff (2026-11-24): the approved plan for turning this repo into a library. Pick it up on x870e at step 1.
> The report builders committed with it (report/build_final.py, cases.py, final_cards.py, input_pages.py,
> single_html.py) rebuild the consolidated report from eval/results (run outputs are not in git; sync them first).

# Plan: turn the plotkit experiment repo into a library for an Electron AI chat app

## Context
The experiments are done. The consolidated report is built by `report/build_final.py`, which writes
`report/plotkit_report.html` (one self-contained file) and `report/plotkit_report.zip`; both are git-ignored and
rebuilt from `eval/results`.

The conclusion for the current plotkit:

- The model writes a **spec**; plotkit draws it.
- **ECharts** is the engine.
- **Reasoning is off by default.** The user can turn it on for tricky asks.
- **No constrained decoding.**

The repo should become an **adaptable library** that the developer of the Electron AI chat app (KetchupE) can
pick up. The front-end integration is hers to design. The library should make it easy and document the
recommended way to use it. The **spec schema becomes a standalone file**: a JSON Schema the TypeScript side can
validate against and generate types from, plus a readable key reference.

Deliverable: a PR from a new branch `lib/plotkit` into `main`. Work continues on x870e. Every step is offline,
with no model calls.

## What the code looks like today (mapped 2026-11-24)
**Entry and routing**
- `plotkit.plot` (`plotkit.py:1556`) is the single entry point:
  - a `chart`, `kind` or `chart_type` key → `chartkit.plot`;
  - a curve with a date x → `chartkit.curve_as_chart`;
  - any other curve → `plotkit_echarts.plot_echarts` or matplotlib.
- chartkit only borrows plotkit's reader, aliases and colours. `chartkit.normalize` rejects curve keys.
- **Router bug:** chartkit aliases `type`, `plot` and `그래프` to `chart` (`chartkit.py:65`), but the router ignores
  them, so such a spec goes down the curve path and fails.
- **Return shapes differ:**
  - charts return `{ok, engine, saved, chart, values, warnings, not_done, summary…}`;
  - curves return `{ok, output_dir, plots[…], warnings, not_done}` and always write `summary.csv`.
  - `not_done` is computed differently in the two paths (`plotkit.py:1764` vs `chartkit.py:2064`).

**Public pieces that already exist**
- plotkit:
  - `inspect_file`, `normalize_spec`, `PlotkitError(message, hint)` (`:41`);
  - the `DEFAULTS` and `SCHEMA_DOC` tables plus the alias tables (`:49-264`); unknown keys get a "did you mean"
    from `_suggest` (`:267`).
- chartkit:
  - `preview` (`:380`), `normalize` (`:168`);
  - `echarts_option` (`:1590`), `live_options` (`:1982`), `schema()` (`:2139`).
- plotkit_echarts: `resolve` (`:330`), `live_options` (`:447`), `ALLOWED`, the echarts-patch allowlist (`:76`).

**Live ECharts option without files**
- **Charts:** pure Python (`chartkit.live_options`).
- **Curves:** Python resolves the figure, then `echartkit/live.mjs` builds the option in Node. `translate.mjs`
  imports nothing and could run directly in the Electron renderer.
- Chart options contain marker strings (`__fmt__…`, `__histbar__`, `__errorbar__`). The page must revive them with
  `revive()`/`formatPy` from `echartkit/render_chart.mjs` (as `eval/live_check.mjs:13` does).
- `eval/cnt_live.py:28` already picks the right live path per spec.

**Node packages**
- `echarts` alone covers the live view and SVG.
- `sharp` is needed for PNG/JPG/TIF.
- `playwright-core` plus Chromium is needed for PDF.

**The v2 model loop lives in `eval/cnt_runs.py`, not `run_agent.py`** (which is v1, TGA only, and uses `/no_think`):
- `system_prompt` = `prompts/v2/core.md` + `hatch_ec.md` (`:76-83`);
- `preview_text` (`:89`): Korean preview lines from `chartkit.preview`;
- `first_message` (`:131`); follow-up turns use `사용자 요청 (이어서):` (`:259`);
- `extract_json` (`:163`): strips `<think>`, takes the first fenced block, then the outermost `{…}`;
- the retry turn `plotkit error: …\nhint: …\n\n고쳐서 다시 보내 주세요.`, at most 2 retries (`:300`);
- reasoning: `chat_template_kwargs.enable_thinking` (`:139`); on Anthropic, `thinking` and `effort` (`eval/cd.py:92`).

**The schema has four sources that drift**
1. `plotkit.DEFAULTS`, `SCHEMA_DOC` and the alias and annotation tables (enforced for curves).
2. chartkit's `TOP_KEYS`, `AXIS_KEYS`, `KINDS`, `AGGS`, `PERIODS` and aliases (`:39-118`).
3. `spec_schema.py`:
   - it copies `KINDS` and `AGGS` by hand;
   - `PERIODS` keeps only the English names;
   - it leaves out `engine`, `notes`, `output.dir` and some aliases;
   - `echarts` is just `{"type":"object"}`;
   - file, sheet and column are always enums from real data, so there is no data-independent schema.
4. `prompts/v2/core.md`: the prose the model reads.

**Dependencies**
- numpy, pandas, scipy (curve peaks), openpyxl, xlrd (optional, `.xls`).
- **matplotlib is required even for ECharts** (colour parsing, nice ticks, heatmap colours).
- jsonschema is used only by `spec_schema.validate`.
- PIL is used only by eval and report code.
- There are no packaging files, and the README install line leaves out pandas.

**Security (matters for a desktop app on Windows/macOS)**
- `sandbox.run` (`data_code` hatch) uses bubblewrap when it is present (Linux only). Otherwise it **silently runs
  model code unsandboxed**.
- It reads the result with **`pickle.load`** (`sandbox.py:91`), so model code can escape into the host process.
- The `code` hatch runs `exec` in-process (`chartkit.py:1475`, `plotkit.py:1714`). The ECharts engine rejects it,
  so the recommended configuration avoids it.

**Side effects:** paths are resolved against the current directory, and `plot` always creates an output folder.

## Target layout
```
plotkit/                    the library (Python package)
  __init__.py               public API (below)
  __main__.py               CLI: python -m plotkit {preview, validate, option, render, schema, prompt, serve}
  core.py                   from plotkit.py   (reader, curves normalize + error/hint, matplotlib engine, router)
  charts.py                 from chartkit.py  (charts, data grammar, preview, chart options)
  echarts.py                from plotkit_echarts.py (curve resolve, patch allowlist)
  sandbox.py                data_code hatch (hardened, below)
  agent.py                  reference loop, ported from eval/cnt_runs.py; the LLM is a callable the app supplies
  prompts/                  core.md, hatch_echarts.md, hatch_matplotlib.md   (git mv from prompts/v2)
  js/                       git mv from echartkit/ (translate, render, render_chart incl. revive, live, dump)
schema/
  plotkit.spec.schema.json  standalone, data-independent JSON Schema (generated)
  SPEC.md                   key reference: every key, default, alias, example (generated from the same tables)
docs/
  INTEGRATION.md            for the app developer
  EXPERIMENTS.md            the conclusion and the evidence index (links experiments/ and the report builder)
experiments/                eval/, gallery/, report/, results/, EXPERIMENT*.md, HANDOFF.md, AGENT*.md (v1),
                            run_agent.py, spec_schema.py's per-request CD use, experiment-only tests and scripts
tests/                      library tests only (offline)
pyproject.toml              deps numpy, pandas, matplotlib, scipy, openpyxl; extras xls (xlrd), schema (jsonschema)
README.md                   library-first
```

## Public API (app-facing, thin)
- `preview(files) -> str`: `preview_text`, moved from `eval/cnt_runs.py`.
- `system_prompt(engine="echarts") -> str`.
- `first_message(request, files)`, `followup_message(request, last_spec)`, `parse_reply(text) -> dict`
  (`extract_json`), `retry_message(err)`.
- `validate(spec) -> dict`: the normalized spec, or raises `PlotkitError(message, hint)`.
- `echarts_options(spec) -> list[dict]`: the live options, without files. It wraps the `eval/cnt_live.py` logic;
  curves still go through Node `live.mjs`.
- `render(spec, out_dir, formats=("png",), engine="echarts")`: export files.
- `request_options(reasoning=False, provider="openai-compatible"|"anthropic") -> dict`: the model settings for the
  recommended configuration. The app's "think harder" toggle passes `reasoning=True`.
- `agent.run(request, files, llm, reasoning=False, history=None)`: the reference loop (preview → model → parse →
  validate, at most 2 retries with error + hint → options), returning `{spec, options, warnings, not_done,
  transcript}`.
- One result shape for curves and charts: `{ok, kind, options, saved, warnings, not_done, values}`.

## Steps
1. **Branch** `lib/plotkit` from `eval/protocol-study` (after pulling this commit on x870e).
2. **Map the blast radius** (read-only; not yet done):
   - every import of the library modules and its `sys.path` setup, across `eval/`, `tests/`, `report/` and
     `gallery/`;
   - hard-coded paths: `ROOT/"echartkit"`, `prompts/v2`, `AGENT*.md`, `tests/inputs`, `eval/cnt`, node script paths,
     JS relative imports such as `eval/render_option.mjs → ../echartkit/`;
   - paths stored in data (the CSV `run_dir` is relative to `eval/`; JSON `file` fields);
   - the offline self-tests and their run times.
3. **Move the experiments first**:
   - `git mv` everything listed under `experiments/` above. Keep `eval/` intact inside it, so `run_dir` stays valid.
   - Fix ROOT, `sys.path` and paths.
   - Re-run the offline self-tests and expect the same numbers:
     - `tests/score.py --reference` (48/48);
     - `eval/validate_checker.py` (233/233);
     - `eval/cd_selftest.py`;
     - `eval/cnt/_selfcheck/selfcheck.py`;
     - `tests/run_tests.py`;
     - `gallery/make_gallery.py`.
   - Commit.
4. **Make the package**:
   - `git mv` the modules, `prompts/v2` and `echartkit/` into `plotkit/`.
   - Fix the imports between modules and the Node paths.
   - Point the experiments at the package (`chartkit` → `plotkit.charts`; shims only where unavoidable).
   - Re-run the self-tests and commit.
5. **Small fixes the library needs**:
   - the router honours every alias of `chart`;
   - one result shape for curves and charts;
   - one shared `not_done`;
   - writing files becomes optional (no forced output folder, no forced `summary.csv`).
   - Re-run the self-tests and commit.
6. **Harden the sandbox**:
   - Replace pickle with JSON/npz for the hatch output.
   - Without bubblewrap, `data_code` is **refused with an error + hint** unless the host passes
     `allow_unsandboxed=True`; never silently.
   - The `code` hatch stays matplotlib-only and off in the recommended configuration.
   - Document it in INTEGRATION.md.
   - Commit.
7. **Add the standalone schema**:
   - Generate it from the Python tables: the plotkit and chartkit key tables, aliases and `plotkit_echarts.ALLOWED`.
     File, sheet and column become strings (columns: a name or a letter pattern).
   - `spec_schema.py` imports `KINDS`, `AGGS` and `PERIODS` instead of copying them.
   - Write `schema/plotkit.spec.schema.json` and `schema/SPEC.md` via `python -m plotkit schema --json|--md`.
   - Tests:
     - every reference spec (`tests/reference_specs.json`, `experiments/eval/reference_b.json`, the CNT dev
       references) validates;
     - a **drift test**: the schema and the normalizers accept the same keys;
     - a test that the committed schema file equals the generated one.
   - Commit.
8. **Add the API, the recommended defaults and the reference loop**:
   - Port `preview_text`, `first_message`, `extract_json`, the retry text and `call_llm`'s
     `chat_template_kwargs`/`thinking` settings from `eval/cnt_runs.py` and `eval/cd.py` into `plotkit/agent.py`.
     The experiment harness then imports them, so there is one copy.
   - Defaults: ECharts, `reasoning=False`. The library has no constrained-decoding path.
   - Add `python -m plotkit serve`: a stdio JSON-lines server (preview, validate, options, render) so Electron can
     run Python as a sidecar.
   - Offline tests with a fake LLM:
     - a good reply gives options;
     - a bad key gets an error + hint, then a retry;
     - reasoning on/off changes only the request options;
     - the follow-up turn includes the last spec.
   - Commit.
9. **Write the docs**:
   - **README**: library-first.
   - **`docs/INTEGRATION.md`**:
     - the message flow;
     - where the preview comes from;
     - error + hint retries hidden from the user;
     - the reasoning toggle;
     - live (options + `revive` in the renderer) vs export (PNG/PDF);
     - the routes: Python sidecar (`serve`) now, porting `translate.mjs` + resolve to TS later;
     - the sandbox notes;
     - known gaps (no keys for legend outside, percent-stacked bars, box plots; asks without a key are dropped
       silently; engine parity bugs).
   - **`docs/EXPERIMENTS.md`**.
   - Commit.
10. **Packaging**:
    - `pyproject.toml`, `npm install --prefix plotkit/js`.
    - In a fresh venv, run `pip install -e .` and then `python -m plotkit prompt|preview|validate|options|render|serve`
      on `tests/inputs/TGA.xlsx` and `experiments/eval/cnt/data/L3_MES_export_202607.csv`.
    - Commit.
11. **PR** `lib/plotkit` → `main`. The description covers the conclusion, the layout, the API, how to integrate,
    the test evidence, and what is left to the app.

## Verification
- Every offline self-test passes after steps 3, 4, 5 and 10, with the same numbers as before the moves.
- The schema validates all reference specs; the drift and up-to-date tests pass.
- Fake-LLM loop tests pass. The `serve` round trip works from a small Node script (as Electron would call it).
- A fresh venv install produces a live option and a PNG for a TGA file and a CNT file.
- No network or model calls anywhere in the tests.
