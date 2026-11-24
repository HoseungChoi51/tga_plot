"""Where things are, now that the experiments live in experiments/ and the library at the repo root.

Requests, reference specs and CSVs name files as the study wrote them, relative to the old one-folder layout:
tests/inputs/... (the library's test files, still at the repo root) and eval/..., gallery/..., prompts/v2lite
(now under experiments/). datapath() finds either; short() turns an absolute path back into that form.
"""
from pathlib import Path

EVAL = Path(__file__).resolve().parent      # experiments/eval
EXP = EVAL.parent                            # experiments/
REPO = EXP.parent                            # the library: plotkit/, tests/inputs, .venv


MOVED = {"prompts/v2": "plotkit/prompts", "echartkit": "plotkit/js"}     # library folders renamed in the package


def datapath(rel):
    """A file name from a request or spec, as an absolute Path. Absolute paths are returned as they are."""
    p = Path(rel)
    if p.is_absolute():
        return p
    for old, new in MOVED.items():
        if p.as_posix() == old or p.as_posix().startswith(old + "/"):
            return REPO / new / p.relative_to(old)
    return REPO / p if (REPO / p).exists() and not (EXP / p).exists() else EXP / p


def hatch(prompt_dir, engine):
    """The engine's hatch file in a prompt folder: plotkit/prompts names them hatch_matplotlib.md / hatch_echarts.md,
    the study's folders (prompts/v2lite) hatch_mpl.md / hatch_ec.md."""
    d = Path(prompt_dir)
    long, short_ = ("hatch_matplotlib.md", "hatch_mpl.md") if engine == "matplotlib" else ("hatch_echarts.md", "hatch_ec.md")
    return d / long if (d / long).exists() else d / short_


def short(path):
    """The study's name for an absolute path: relative to experiments/ if it is inside, else to the repo."""
    p = Path(path)
    return p.relative_to(EXP) if p.is_relative_to(EXP) else p.relative_to(REPO)
