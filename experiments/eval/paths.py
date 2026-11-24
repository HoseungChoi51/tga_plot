"""Where things are, now that the experiments live in experiments/ and the library at the repo root.

Requests, reference specs and CSVs name files as the study wrote them, relative to the old one-folder layout:
tests/inputs/... (the library's test files, still at the repo root) and eval/..., gallery/..., prompts/v2lite
(now under experiments/). datapath() finds either; short() turns an absolute path back into that form.
"""
from pathlib import Path

EVAL = Path(__file__).resolve().parent      # experiments/eval
EXP = EVAL.parent                            # experiments/
REPO = EXP.parent                            # the library: plotkit, tests/inputs, prompts, echartkit, .venv


def datapath(rel):
    """A file name from a request or spec, as an absolute Path. Absolute paths are returned as they are."""
    p = Path(rel)
    if p.is_absolute():
        return p
    return REPO / p if (REPO / p).exists() and not (EXP / p).exists() else EXP / p


def short(path):
    """The study's name for an absolute path: relative to experiments/ if it is inside, else to the repo."""
    p = Path(path)
    return p.relative_to(EXP) if p.is_relative_to(EXP) else p.relative_to(REPO)
