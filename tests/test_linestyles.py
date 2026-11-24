"""Every spelling of a line style draws the same on ECharts as its canonical name (it used to draw solid)."""
from pathlib import Path

import pytest

import plotkit
from conftest import ENGINES
from plotkit import core

INPUTS = Path(__file__).resolve().parent / "inputs"
SPELLINGS = sorted(core.LINESTYLES)                     # "--", "점선", "dotted", "-.", "일점쇄선", ...


def y2_dash(ls):
    o = plotkit.echarts_options({"file": "TGA.xlsx", "sheets": 1, "y2": {"linestyle": ls}}, INPUTS)[0]
    return next(s["lineStyle"]["type"] for s in o["series"] if s.get("yAxisIndex") == 1)


def vline_dash(ls):
    o = plotkit.echarts_options({"file": "TGA.xlsx", "sheets": 1,
                                 "annotate": {"v": {"type": "vline", "x": 450, "linestyle": ls}}}, INPUTS)[0]
    return next(m["lineStyle"]["type"] for s in o["series"] for m in (s.get("markLine") or {}).get("data", [])
                if m.get("xAxis") == 450)


def ref_dash(ls):
    o = plotkit.echarts_options({"file": "run_log.csv", "chart": "bar", "x": "반응기", "y": "수율",
                                 "ref": [{"y": 4.2, "linestyle": ls}]}, INPUTS)[0]
    return next(m["lineStyle"]["type"] for s in o["series"] for m in (s.get("markLine") or {}).get("data", []))


@pytest.mark.parametrize("ls", SPELLINGS)
def test_every_spelling_draws_like_its_name(ls):
    name = core.linestyle_name(ls, "test")
    assert y2_dash(ls) == y2_dash(name)
    assert vline_dash(ls) == vline_dash(name)
    assert ref_dash(ls) == ref_dash(name)


def test_the_four_styles_differ():
    assert len({str(y2_dash(n)) for n in ("solid", "dashed", "dotted", "dashdot")}) == 4
    assert len({str(ref_dash(n)) for n in ("solid", "dashed", "dotted", "dashdot")}) == 4


def test_unknown_style_is_an_error_with_a_hint():
    for spec in ({"file": "TGA.xlsx", "y2": {"linestyle": "wavy"}},
                 {"file": "TGA.xlsx", "annotate": {"v": {"type": "vline", "x": 450, "linestyle": "wavy"}}}):
        with pytest.raises(plotkit.PlotkitError) as e:
            plotkit.validate(spec, INPUTS)
        assert "solid, dashed, dotted or dashdot" in e.value.hint


@pytest.mark.parametrize("engine", ENGINES)
def test_both_engines_draw_korean_styles(engine, tmp_path):
    spec = {"file": "TGA.xlsx", "sheets": 1, "y2": {"linestyle": "점선"},
            "annotate": {"v": {"type": "vline", "x": 450, "linestyle": "일점쇄선"}}}
    assert plotkit.render(spec, tmp_path, engine=engine, base=INPUTS)["saved"]
