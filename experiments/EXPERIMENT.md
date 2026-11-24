# Engine experiment: can the same model drive ECharts?

The question: with Pi and the same local model, are the 24 requests in
`tests/AGENT_TEST_PROMPTS.md` answered as well when ECharts draws the plot as when matplotlib does?
If yes, KetchupE can keep its ECharts engine and adopt plotkit's protocol (a small spec with
defaults, `error` + `hint` feedback, the part-name glossary) instead of shipping Python.

plotkit still reads the files and computes the residue and peaks in Python for both engines, so
the only differences between the arms are the drawing engine and the instructions for things no
key covers (`code` in matplotlib, `echarts` in ECharts).

| arm | instructions | engine | for things no key covers |
|---|---|---|---|
| 0 | `AGENT.md` (unchanged) | matplotlib | `"code"`: Python |
| S | `AGENT_ECHARTS.md` | ECharts | `"echarts"`: a JSON patch checked against an allowlist; plus the new `band` annotation |

`AGENT_ECHARTS.md` differs from `AGENT.md` only in the "Extra ECharts settings" section, one
`band` row in the table and the shading example (`diff AGENT.md AGENT_ECHARTS.md`).

## Set up (once)

    pip install numpy matplotlib scipy openpyxl xlrd
    npm install --prefix echartkit                  # Node.js 20+; ECharts 6.1.0 and sharp, as in KetchupE
    npx --prefix echartkit playwright install chromium     # only for PDF output (request 14)
    python tests/score.py --reference               # harness check: all 48 must pass (24 requests x 2 engines)

For PDF you can instead point `PLOTKIT_CHROMIUM` at an installed Chrome or Chromium. On Windows,
Edge is used automatically if nothing else is found.

## Run an arm with Pi

Start Pi in this folder with the arm's instruction file, and the engine in the environment:

    # arm 0
    pi ...  (instructions: AGENT.md)
    # arm S
    PLOTKIT_ENGINE=echarts pi ...  (instructions: AGENT_ECHARTS.md)
    #   Windows PowerShell:  $env:PLOTKIT_ENGINE = "echarts"; pi ...

For each request, in a fresh session:

1. Paste the request from `tests/AGENT_TEST_PROMPTS.md` and time it, from paste to the final answer.
2. Score the spec it saved (`spec.json`), with the time and the number of `plot` runs you saw:

       python tests/score.py --arm S --request 07 --seconds 41 --calls 2

   This re-draws the spec with the arm's engine into `results/out/<arm>/<request>/`, checks the facts
   in `tests/expected_requests.json`, appends a row to `results/arm<arm>.csv` and keeps the spec in
   `results/specs/`. The engine follows the arm, so a session started without `PLOTKIT_ENGINE` is
   still scored with the right engine.
3. Delete `tests/inputs/*_plots/` before the next request.

When an arm is done:

    python tests/contact_sheet.py         # results/contact_sheet.html: arm 0 and arm S images side by side

Open it and note any request where the change asked for is not visible.

## Batch runs (repeatable, no Pi)

`run_agent.py` makes one model call per request (with the `inspect` output given) and up to 2
retries with plotkit's `error` + `hint`. It is less realistic than Pi but easy to repeat:

    python run_agent.py --base-url http://localhost:11434/v1 --model <name> --no-think \
        --engine matplotlib --batch tests/AGENT_TEST_PROMPTS.md --repeat 3      # -> results/batch_0.csv
    python run_agent.py --base-url http://localhost:11434/v1 --model <name> --no-think \
        --engine echarts --batch tests/AGENT_TEST_PROMPTS.md --repeat 3         # -> results/batch_S.csv

`--only 07,20` runs a few requests again.

## Reading the result

| result | meaning for KetchupE |
|---|---|
| S within 1 request of 0, all changes visible | ship the spec + a TypeScript translator to ECharts; port the reader and annotation maths |
| S loses 2+ requests to drawing gaps | fix `echartkit/translate.mjs`, rerun only those requests |
| S loses requests because the model misuses `band` or `echarts` | improve `AGENT_ECHARTS.md` for those keys; the engine is fine |

## Windows check (once)

On a Windows PC with a Korean locale, from a folder whose path has Korean letters and spaces:

    python tests/render_all.py --engine echarts               # the specs the model wrote (results/specs/S_*.json)
    python tests/render_all.py --engine echarts --reference   # or the reference specs

Check the Korean text in the PNGs (sharp draws them with its own font lookup) and in the PDF of
request 14 (Chromium/Edge uses the system fonts).

## Known differences (ECharts vs matplotlib)

- `tick_direction: "inout"` has no ECharts setting; it is drawn as longer outward ticks, with a warning.
- With `step` and a `min` that is not a multiple of `step`, ticks still start at `min` (as in matplotlib).
- Text sizes are estimated without font metrics, so label boxes can be a few pixels off.
- The `echarts` patch can restyle anything on the allowlist, so it can also undo what keys set.
