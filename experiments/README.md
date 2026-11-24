# experiments/

The studies that chose plotkit's design: the protocol evaluation (TGA, six arms), the CNT plant study (layer v2),
the reasoning and constrained-decoding runs, the engine parity, coverage and safety checks, and the gallery.
The conclusion and the evidence index are in `../docs/EXPERIMENTS.md`.

Everything here was moved from the repo root on 2026-11-24, when the repo became a library. The documents in this
folder (`HANDOFF.md`, `EXPERIMENT.md`, `EXPERIMENT_CD.md`, `AGENT*.md`, `eval/cnt/README.md`) were written before
the move. Read their paths like this:

| written as | now |
|---|---|
| `eval/`, `gallery/`, `report/`, `results/`, `guide/`, `old/`, `examples/` | `experiments/eval/`, ... |
| `run_agent.py`, `spec_schema.py`, `AGENT.md`, `AGENT_ECHARTS.md` | `experiments/...` |
| `tests/score.py`, `tests/expected_requests.json`, `tests/AGENT_TEST_PROMPTS.md`, `tests/contact_sheet.py`, `tests/render_all.py` | `experiments/tests/...` |
| `prompts/v2lite/` | `experiments/prompts/v2lite/` |
| `tests/inputs/`, `tests/reference_specs.json`, `tests/run_tests.py` | unchanged: these are the library's tests |

Run the scripts from the repo root, e.g. `python experiments/eval/validate_checker.py`.

File names inside requests, reference specs and run records keep the form the study used (`tests/inputs/TGA.xlsx`,
`eval/inputs_b/caox.csv`). `eval/paths.py` resolves both forms. The CSV `run_dir` column is relative to `eval/`, as
before.

## Offline self-tests (no model calls)

| command | expected |
|---|---|
| `python experiments/tests/score.py --reference` | ALL PASSED (24 requests x 2 engines) |
| `python experiments/eval/validate_checker.py` | agreement 233/233 (fact pass 189) |
| `python experiments/eval/cd_selftest.py` | replay P-ec 179/151/179, P-mpl 179/152/177, TGA 53/53/53; flat 411/409/411 |
| `python experiments/eval/cnt/_selfcheck/selfcheck.py` | 28/28 checks passed |
| `python experiments/gallery/make_gallery.py` | 26 specs x 2 engines (25 and 26 refused on the other engine) |
| `python tests/run_tests.py` | ALL PASSED (the library's reader test) |

`make_gallery.py` rewrites `gallery/data/*.xlsx` with a new timestamp; `git checkout experiments/gallery/data` undoes it.
