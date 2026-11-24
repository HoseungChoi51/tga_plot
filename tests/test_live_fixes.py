"""The live curve option and the static render agree on the model's "echarts" patch, and every line label lands on
its own line (fixes found by the TypeScript port, ts/: the same tests run there on these specs)."""
import json
import re
from pathlib import Path

import pytest

import plotkit
from plotkit import api, echarts

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "tests" / "inputs"
BASE = {"file": "TGA.xlsx", "sheets": 1}


def live(spec):
    return echarts.live_result(api.with_base(spec, INPUTS))


def static(spec, tmp_path, monkeypatch):
    """The static render's SVG text and the option it drew (render.mjs's PLOTKIT_DUMP_OPTION)."""
    dump = tmp_path / "dump.json"
    monkeypatch.setenv("PLOTKIT_DUMP_OPTION", str(dump))
    r = plotkit.render(spec, tmp_path / "out", formats=("svg",), base=INPUTS)
    figs = json.loads(dump.read_text(encoding="utf-8"))["figures"]
    return [Path(p).read_text(encoding="utf-8") for p in r["saved"]], [f["option"] for f in figs]


def test_live_merges_the_patch_as_the_static_render(tmp_path, monkeypatch):
    patch = {"xAxis": {"inverse": True, "minorTick": {"show": True}}, "grid": {"right": 120},
             "series": [{"lineStyle": {"type": "dotted"}}, {}],
             "yAxis": [{"name": "TG"}],
             "graphic": [{"type": "text", "right": 10, "top": 10, "style": {"text": "note"}}]}
    o = live({**BASE, "echarts": patch})["options"][0]
    assert o["xAxis"]["inverse"] is True and o["xAxis"]["minorTick"]["show"] is True
    assert o["grid"]["right"] == 120 and o["yAxis"][0]["name"] == "TG"
    assert o["series"][0]["lineStyle"]["type"] == "dotted"
    assert o["series"][1]["lineStyle"]["type"] == "solid"                    # {} leaves series 1 as it is
    assert o["graphic"] == {"elements": patch["graphic"]}
    assert o["tooltip"] and o["dataZoom"]                                    # still the live chart
    _, [s] = static({**BASE, "echarts": patch}, tmp_path, monkeypatch)
    assert s["xAxis"][0]["inverse"] is True and s["grid"][0]["right"] == 120 and s["yAxis"][0]["name"] == "TG"
    assert s["series"][0]["lineStyle"]["type"] == "dotted"


def test_live_without_a_patch_is_unchanged():
    o = live(BASE)["options"][0]
    assert "graphic" not in o and o["xAxis"]["inverse"] is False and o["grid"]["right"] != 120


def test_live_refuses_too_many_series_as_the_static_render(tmp_path):
    spec = {**BASE, "echarts": {"series": [{}, {}, {"name": "x"}]}}
    with pytest.raises(plotkit.PlotkitError) as live_err:
        live(spec)
    with pytest.raises(plotkit.PlotkitError) as static_err:
        plotkit.render(spec, tmp_path, formats=("svg",), base=INPUTS)
    assert live_err.value.message == static_err.value.message == "echarts.series has 3 entries but this plot has 2"
    assert live_err.value.hint == static_err.value.hint == "series: 0 = y1 1006R1-V normal, 1 = y2 1006R1-V normal"


def test_line_labels_stay_on_their_own_lines():
    spec = {**BASE, "annotate": {"onset": {"type": "vline", "x": 300, "text": "onset"},
                                 "limit": {"type": "hline", "y": 0.3, "on": "y2", "text": "limit"},
                                 "mass": {"type": "hline", "y": 0.3, "on": "y1", "text": "same value"},
                                 "quiet": {"type": "hline", "y": 0.5, "on": "y2"}}}
    o = live(spec)["options"][0]
    marks = {s["name"]: s["markLine"]["data"] for s in o["series"] if s["name"].startswith("__marks_")}
    y1 = [(d.get("xAxis"), d.get("yAxis"), d["label"].get("formatter")) for d in marks["__marks_y1"]]
    y2 = [(d.get("xAxis"), d.get("yAxis"), d["label"].get("formatter")) for d in marks["__marks_y2"]]
    assert y1 == [(300, None, "onset"), (None, 0.3, "same value")]
    assert y2 == [(None, 0.3, "limit"), (None, 0.5, None)]
    assert marks["__marks_y2"][1]["label"] == {"show": False}


def test_renamed_series_keep_their_legend(tmp_path, monkeypatch):
    spec = {**BASE, "echarts": {"series": [{"name": "Mass"}, {"name": "DTG"}]}}
    o = live(spec)["options"][0]
    assert [s["name"] for s in o["series"][:2]] == ["Mass", "DTG"] and o["legend"]["data"] == ["Mass", "DTG"]
    [svg], [s] = static(spec, tmp_path, monkeypatch)
    assert s["legend"][0]["data"] == ["Mass", "DTG"]
    texts = re.findall(r">([^<>]+)</text>", svg)
    assert "Mass" in texts and "DTG" in texts and "Weight (%)" in texts       # legend keys; y1 axis name kept


def test_renamed_combined_sheets_share_one_entry():
    spec = {"file": "TGA.xlsx", "combine": True,
            "echarts": {"series": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "A"}, {"name": "B"}, {"name": "C"}]}}
    o = live(spec)["options"][0]
    assert o["legend"]["data"][:3] == ["A", "B", "C"] and len(o["legend"]["data"]) == len(set(o["legend"]["data"]))
