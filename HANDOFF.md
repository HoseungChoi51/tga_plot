# Handoff: plotkit protocol evaluation (2026-11-18)

This file is for whoever continues the evaluation on another machine (you, or Claude Code
opened in this repo). Read it top to bottom once. Everything the evaluation needs is under
`eval/`. The report generator is `report/build_report.py`.

## The questions

The plotkit protocol is the AGENT.md glossary, plus a small JSON spec with defaults, plus `error`/`hint`
feedback, drawn by matplotlib or ECharts. It is meant to make an LLM plot reliably, giving up some
freedom. The user asked for a report on three questions:

1. **Does it help?** Compare the same model writing plotting code directly.
2. **Does it cover reasonable variety?**
3. **How does it connect to the back-end libraries?**

Decisions already made by the user:
- Model: Qwen3.8 Flash Next only.
  - Batch harness for all arms, plus a small Pi agent-session subset.
  - Raw-code baseline in two variants, plain and with a TGA brief.
- Report: a **published private HTML page** (claude.ai artifact). Scripts and CSVs stay in this repo.
- Taking long is fine.

## Design (six arms)

| arm | the model gets | it writes | drawn by |
|---|---|---|---|
| P-mpl / P-ec | AGENT.md / AGENT_ECHARTS.md | JSON spec | plotkit (matplotlib / ECharts) |
| R-mpl-brief / R-ec-brief | short prompt + TGA brief (conventions, Korean part names; no spec) | Python script | the script / its printed ECharts option (ECharts 6.1 SSR) |
| R-mpl-plain / R-ec-plain | short prompt only | Python script | as above |

Every arm gets the same things:
- the same data preview (plotkit `inspect`)
- a 16k-token cap
- at most 2 retries with the error it caused

Raw scripts run in **bubblewrap**, with no network and a read-only filesystem except the run folder.

The requests are split into two sets:
- **Set A**: the 24 requests in `tests/AGENT_TEST_PROMPTS.md`.
- **Set B**: 24 new ones in `eval/requests_b.md`, using data in `eval/inputs_b/`.
  - groups: in-scope but not rehearsed (7), messy wording (6), no spec key (11)
  - B05 was moved to "out": no key renames combined curves.

Scoring is the same for every arm:
- `eval/facts.py` extracts **figure facts** from what was actually drawn:
  - matplotlib: from the Figure objects.
  - ECharts: from the final option plus the axis extents and texts ECharts computed.
  - ECharts dump: `PLOTKIT_DUMP_OPTION=<file>`, implemented in `echartkit/dump.mjs`.
- `eval/check.py` runs one checker over them.
- `eval/expected_facts.json` holds the checks, built by `eval/expectations.py` and `eval/requests_b.py`.
- Each check has a category:
  - `data`: right data drawn
  - `ask`: what was asked
  - `conv`: lab conventions such as residue and peak labels

## What is done (results in `eval/results/`)

- **Checker validated:** `eval/validate_checker.py` → 233/233 agreement with the old spec scorer.
  - Covers reference specs, Odin's earlier specs, bare-spec negative controls and Set B reference answers (`eval/reference_b.json`).
- **Parity** (`eval/parity.py` → `parity.csv`): 69 specs on both engines, 11 differ. Confirmed:
  - Linestyle aliases `"--"` / `"점선"` draw **solid** in ECharts. Bug: `translate.mjs` `dash()` only knows canonical names.
  - A residue label beyond `x.max` is drawn outside the plot in ECharts; matplotlib omits it.
  - Automatic ticks differ on small or large-font figures, and are crowded in ECharts.
  - `inout` ticks are approximated in ECharts.
- **Latency** (`latency.csv`), median per figure:
  - PNG: matplotlib 0.17 s, ECharts 0.49 s (about 0.34 s of that is a Node cold start on every plot).
  - PDF: 0.27 s vs 1.09 s.
- **Coverage** (`eval/coverage.py` → `coverage.csv`), 64 plausible wishes, each route drawn or refused for real:

  | route | matplotlib | ECharts |
  |---|---|---|
  | key (both engines) | 38 | 38 |
  | escape hatch | +25 via `code` | +11 via the patch, +3 partial |
  | no route | 1 | 12 |

  - ECharts can't do: legend renames when combined (`legend.data` not allowed), second x axis, unit-converted axis, two panels, inset, offset curves, onset, Δmass, normalisation, computed DTG, error bands.
- **Safety** (`safety.json`): `code` runs arbitrary Python with no sandbox (read a file outside, list home, start a process). The ECharts patch refuses functions, URLs and data.
- **Gallery** (`gallery/`): 26 specs × 2 engines. Rebuild with `python gallery/make_gallery.py --pages`.
- **Odin (office server, centinels) findings**, kept as a reference:
  - Spec arms passed 24/24 on both engines at temperature 0: `results/batch_0.csv`, `results/batch_S.csv`, specs in `results/odin_specs.md`.
  - With thinking on, raw-code arms often spend more than 16k reasoning tokens self-reviewing ("Potential issue: …") and return no code. At temperature 0 this happened on every call checked.
  - Evidence: `eval/results/batch_t0_aborted.csv`, `batch_t06.csv`, reasoning traces in `eval/results/runs/t0_aborted|t06/*/reasoning_*.txt`.
  - `chat_template_kwargs.enable_thinking=false` switches thinking off; `/no_think` is ignored.
  - Odin was also queue-limited (spec calls waited more than 12 min under load), so the study moved to Strix Halo.

## State of the main run (stopped on the laptop; continue on the new machine)

The main run uses the user's home Strix Halo (`strixhalo` on the tailnet):
- Endpoint: `http://strixhalo:8084/v1`, model `qwen3.8-flash-next`, a UD-Q4_K_XL GGUF with MTP.
- The server has `--sessions 2`, so it serves 2 requests at a time.

Settings:
- Thinking off, the mode `run_agent.py --no-think` recommends for Qwen.
- Temperature 0.7, 3 repeats, 864 runs in all.

```
EVAL_API_KEY_FILE=~/.config/strixhalo_key python eval/run_batch.py --name sx \
  --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next --no-think --temperature 0.7 --repeat 3 --workers 3
```

**On the laptop it was stopped at 119/864 runs**, all from repeat 1. Strix Halo was released: it showed no client connections and was idle.

The commit holds the finished part:
- `eval/results/batch_sx.csv`
- every finished run's record, replies and scripts under `eval/results/runs/sx/`
- their images, force-added so the blind review can use them; later run images are git-ignored again

Runs that were cut off mid-way were deleted. They are not in the CSV, so they will run again.

**To continue on the new machine:**
1. `git pull`.
2. Rerun the command above. Rows already in the CSV are skipped.
3. Don't run two machines against Strix Halo at once; it only has 2 slots.

**Rescore after the run.** The checker was changed while the run was going: ECharts font sizes are now accepted in px or pt, since an ECharts `fontSize: 18` is px. Run `python eval/rescore.py --name sx`. It re-checks every row from its `record.json` without calling the model.

## Set up a new machine

1. `git checkout eval/protocol-study`, the branch this was pushed to.
2. Python 3.13 venv in `.venv`: `uv venv && uv pip install numpy matplotlib scipy openpyxl xlrd pandas pillow`.
3. `npm install --prefix echartkit` (Node 20+), then `npx --prefix echartkit playwright install chromium` for PDF output.
4. System packages:
   - `bubblewrap`: the raw-code sandbox.
   - a Korean font, e.g. `fonts-noto-cjk`. The prompts tell the model "Noto Sans CJK KR is installed".
5. Tailnet access to `strixhalo:8084` and the API key. Unauthenticated calls get HTTP 401. Write the key to a file without printing it:
   ```
   ssh strixhalo 'docker inspect -f "{{json .Config.Cmd}}" qwen38-flash-next' \
     | python3 -c "import sys,json;c=json.load(sys.stdin);print(c[c.index('--api-key')+1])" > ~/.config/strixhalo_key
   chmod 600 ~/.config/strixhalo_key
   ```
6. Check the harness:
   - `python tests/score.py --reference` should report ALL PASSED.
   - `python eval/validate_checker.py` should report agreement 233/233. It needs `results/batch_0.csv` and `batch_S.csv`, which are committed.

Absolute paths: scripts written by the model contain absolute data paths of the machine they ran on. The CSV's `run_dir` is relative to `eval/`, so review and report work anywhere.

## Constrained decoding (added 2026-11-23)

`EXPERIMENT_CD.md` covers it: the `+cd` / `+cdflat` arms, `eval/cd_preflight.py` (run it first against the server),
`eval/cd_compare.py`, and the Anthropic backend used as a small-model stand-in (Haiku 5.5, low effort, thinking off).

## What is left, in order

1. **Finish the `sx` batch**, then run `python eval/rescore.py --name sx`.
2. **Thinking-on check** (small). It shows what thinking costs: Odin data says runaway reasoning on raw code. Suggested command:
   ```
   python eval/run_batch.py --name sx_think --base-url http://strixhalo:8084/v1 --model qwen3.8-flash-next \
     --temperature 0.6 --only 02,09,12,20,23,B02,B06,B11,B15,B18,B21,B23 --arms P-mpl,P-ec,R-mpl-brief,R-ec-brief --workers 3
   ```
3. **Pi agent sessions**: `eval/pi_runs.py`, 12 requests × P-mpl, P-ec, R-mpl-brief, run in clean workspaces with no answer files.
   - Pi needs a provider for Strix Halo in `~/.pi/agent/models.json`: `"strixhalo": {"baseUrl": "http://strixhalo:8084/v1", "api": "openai-completions", "models": [{"id": "qwen3.8-flash-next"}]}`, plus the key, via `pi auth` or the provider's key setting.
   - Check it with `pi --list-models strixhalo`.
   - Run `python eval/pi_runs.py --pi-model strixhalo/qwen3.8-flash-next --thinking off`.
   - Verify in one `session.jsonl` that thinking is really off: reasoning tokens should be about 0.
   - The harness was tested end to end once on Odin: P-mpl request 12 passed, but the session ran into the timeout. That row is in `pi_harness_test.csv`.
4. **Blind visual review**:
   - `python eval/review_sheets.py --run sx` makes one page per request, arms shuffled as A–F.
   - Grade them into `eval/results/review/sx/grades.csv` with columns `request,label,verdict(yes|partial|no),defects`, without opening `key.json`.
   - Then `--unblind`.
5. **Analysis and report**:
   - `python report/build_report.py` reads `eval/results/*`.
   - It points at `batch_t0.csv` today. Switch `load()` to `batch_sx.csv`, and use the repeats for variance: pass rate per request across the 3 repeats.
   - Fill the placeholders `__HELP_DETAIL__`, `__COVER_DETAIL__`, `__BACKEND_DETAIL__`, `__EXAMPLES__`, `__T07__`, `__PI__`, `__REVIEW__`, `__OUTSCOPE__`, `__MAPPING__`, `__RECS__`, `__REPRO__`, `__SPEC_S__`.
   - Then publish `report/index.html` + `report/img/` as a private artifact (claude-artifacts `publish_files`), with title "plotkit protocol evaluation".
   - The page must state the caveats: one model (quantized, thinking off), requests written by the protocol's author for Set A, synthetic data, batch mode vs Pi.

## Things to know

- Earlier spec-based checks were biased toward plotkit's own formatting. They were relaxed with `any_of` so raw code isn't failed for readings the user didn't rule out:
  - Request 02 accepts any decimals in "Residue {}%", and accepts the DTG max value or the peak temperature.
  - Request 03 accepts peak temperatures or peak DTG values.
  - Request 23 accepts any decimals.
  - B11's tolerance was loosened.
- `pkill -f "<pattern>"` also matches the shell that runs it if the pattern is in its own command line, and kills it. Use `ps … | grep "[e]val/…"` to find the PIDs instead.
- `.venv` was made with uv, which has no `pip`. A *symlinked* venv python loses the venv, so Pi workspaces use wrapper scripts in `bin/`.
- `plots_out/` and `plots_out.zip` are the user's own untracked files and were deliberately not committed.
- The plan this follows is in Claude Code's plan file for this session; this document supersedes it.
