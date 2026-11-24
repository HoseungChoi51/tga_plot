# What the experiments decided, and where the evidence is

plotkit began as an experiment: can a language model make the plots a lab needs (TGA curves, then general
production charts) more reliably and more cheaply by writing a small JSON spec that a tool draws, instead of writing
plotting code? About 6,800 scored runs later, on two machines and three model servers, the answer shaped this
library. The code and the results of those studies are in [`experiments/`](../experiments/README.md).

## The conclusion the library is built on

- **The model writes a spec; plotkit draws it.** Where a key covers the ask, the spec path is reliable and cheap:
  93–94% of keyed TGA requests on both models tried (Qwen3.8 Flash Next on a local server, GPT-6 Luna), at about
  50 output tokens and a few seconds. Raw plotting code needed 600–2,500 tokens and up to two minutes, misread the
  lab's own terms, tripped on awkward files, and its plots were rejected far more often in blind review (clutter,
  overlapping text).
- **ECharts is the engine.** The app (KetchupE) shows charts with ECharts, and the library gives it live options
  (labels tied to the data, zoom, tooltip) plus SVG/PNG/PDF exports from the same spec. matplotlib stays as the
  second engine. The report recommended matplotlib for exports; the plan chose one engine for both, with the known
  parity bugs listed below.
- **Reasoning is off by default; the user can turn it on.** Reasoning helped the spec path by 13–16 points on keyed
  asks, but costs time and tokens on every request, and on ECharts a no-key ask could trap the model (46k tokens,
  nothing drawn). Off by default with a "think harder" toggle keeps the common case fast. Raw code with thinking on
  ran past its budget and drew nothing on Qwen-class models.
- **No constrained decoding.** Free decoding plus plotkit's error + hint already passed 95–98% where keys exist.
  Forcing the reply through a JSON Schema did not help on one server (−5 / −3 points, not significant) and dropped
  keys silently on another, whose grammar only accepts keys in alphabetical order (−16 to −92 points).
- **The main weakness is silent.** When no key covers an ask, the model writes the nearest key, plotkit accepts it,
  and the plot quietly differs: 21–42% on no-key asks, against 58–88% for raw code. The spec's `asks` list (with
  `how: "unsupported"`, returned as `not_done`) is the library's answer for now: the app should tell the user.

## Where the evidence is

| what | where |
|---|---|
| The consolidated report: every claim with the request, the prompt, the model's reply and the plot | `python experiments/report/build_final.py` writes `experiments/report/plotkit_report.html` (one file) and a zip; the run outputs it reads are synced, not in git |
| The TGA protocol study: six arms (spec vs raw code, two engines), Set A + B, checker, parity, coverage, safety | `experiments/HANDOFF.md`, `experiments/EXPERIMENT.md`, `experiments/eval/` |
| The CNT study (layer v2: general charts, multi-turn sessions, a sealed split) | `experiments/eval/cnt/README.md`, `experiments/eval/cnt_runs.py` |
| Constrained decoding | `experiments/EXPERIMENT_CD.md`, `experiments/eval/cd*.py`, `experiments/spec_schema.py` |
| Result tables (one CSV per run, the record of every run) | `experiments/eval/results/` |
| The gallery: 26 specs on made-up data, both engines | `python experiments/gallery/make_gallery.py` |

The offline self-tests that check the harness (no model calls) are listed in
[`experiments/README.md`](../experiments/README.md). They give the same numbers before and after the move into this
layout.

## Limits of the evidence

Two models on TGA (one quantized and local, one through a proxy that refused many raw-code calls), one model family
on the CNT charts; synthetic data; the protocol's author wrote the first request set. Scores come from a
figure-facts checker validated against hand-written answers and negative controls; it does not see layout.
Reviewers and personas were Claude sessions.

## Known gaps carried into the library

- No keys yet for: percent-stacked bars (`percent` is accepted and ignored), box plots, colour rules, unit
  conversions and computed curves (onset, mass loss, dry basis, DTG from weight).
- Asks with no key are not refused by plotkit; only the model's `asks` list reports them.
- Engine parity: line-style aliases such as `"--"` and `"점선"` draw solid on ECharts; a residue label beyond `x.max`
  is drawn outside the plot on ECharts (matplotlib leaves it out); automatic ticks differ on small or large-font
  figures; `inout` ticks are approximated on ECharts.
