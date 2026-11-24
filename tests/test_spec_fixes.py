"""The spec check's fixes: inputs that crashed with a Python exception now give a PlotkitError with a hint, the caller's
spec is left as it is, and a few chart keys behave as their curve counterparts (the TS port, ts/src/spec.ts and
chartspec.ts, gives the same results: ts/test/spec.test.ts)."""
import copy

import pytest

from plotkit import charts, core
from plotkit.core import PlotkitError

CURVE = {"file": "TGA.xlsx"}
CHART = {"file": "run_log.csv", "chart": "bar", "x": "반응기"}
TYPES = "types: band, hline, peak, text, value_at_x, vline"
FLIP = "use none, flip, peaks_up or peaks_down"
FORMATS = "use png, pdf, svg, jpg or tif"
COUNT = 'e.g. "count": 2'
CODE = "write the code as one string, or as a list of strings (one per line)"
LEGEND = '"legend" must be a position text, false, or {"where": ..., "show": ..., "size": ...}'
LEGEND_HINT = 'e.g. "legend": "upper right", "legend": false or "legend": {"where": "outside right"}'
POINT_HINT = 'e.g. "point_size": 30 (one marker size for all points; sizes from a column are not supported)'


def curve(**k):
    return core.normalize_spec({**CURVE, **k})


def chart(**k):
    return charts.normalize({**CHART, **k})


def error(f, spec):
    with pytest.raises(PlotkitError) as e:
        f(spec)
    return e.value.message, e.value.hint


@pytest.mark.parametrize("spec, message, hint", [
    ({**CURVE, "y2": {"flip": [1]}}, "y2.flip [1] unknown", FLIP),
    ({**CURVE, "y1": {"flip": {"a": 1}}}, "y1.flip {'a': 1} unknown", FLIP),
    ({**CURVE, "annotate": {"p": {"type": ["peak"]}}}, "annotate.p.type ['peak'] unknown. Did you mean \"peak\"?", TYPES),
    ({**CURVE, "annotate": {"p": {"type": {"t": "band"}}}}, "annotate.p.type {'t': 'band'} unknown.", TYPES),
    ({**CURVE, "legend": {"where": ["upper right"]}}, "legend position ['upper right'] unknown",
     "use one of: " + ", ".join(core.LEGEND_PLACES)),
    ({**CURVE, "annotate": {"peak": {"count": None}}}, "annotate.peak.count must be a whole number of 1 or more, got None", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": "inf"}}}, "annotate.peak.count must be a whole number of 1 or more, got 'inf'", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": "nan"}}}, "annotate.peak.count must be a whole number of 1 or more, got 'nan'", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": "two"}}}, "annotate.peak.count must be a whole number of 1 or more, got 'two'", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": 2.5}}}, "annotate.peak.count must be a whole number of 1 or more, got 2.5", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": 0}}}, "annotate.peak.count must be a whole number of 1 or more, got 0", COUNT),
    ({**CURVE, "annotate": {"peak": {"count": True}}}, "annotate.peak.count must be a whole number of 1 or more, got True", COUNT),
    ({**CURVE, "data_code": ["x = x", 5]}, '"data_code" must be text or a list of text lines, got 5 in the list', CODE),
    ({**CURVE, "code": ["a", {"b": 1}]}, "\"code\" must be text or a list of text lines, got {'b': 1} in the list", CODE),
    ({**CURVE, "output": {"format": None}}, "output.format None not supported", FORMATS),
    ({**CURVE, "format": 5}, "output.format 5 not supported", FORMATS),
    ({**CURVE, "output": {"format": True}}, "output.format True not supported", FORMATS),
    ({**CURVE, "x": "B", "x.min": 0}, "\"x\" is given twice: as 'B' and through \"x.min\"",
     'write "x" once, as one object, e.g. "x": {"col": ..., "min": ...}'),
    ({**CURVE, "x.min": 0, "x": "B"}, "\"x\" is given twice: as 'B' and through \"x.min\"",
     'write "x" once, as one object, e.g. "x": {"col": ..., "min": ...}'),
    ({**CURVE, "output": "png", "format": "pdf"}, "\"output\" is given twice: as 'png' and through \"format\"",
     'write "output" once, as one object, e.g. "output": {"format": ...}'),
    ({**CURVE, "y2.color": "red", "y2": False}, '"y2" is given twice: as False and through "y2.color"',
     'write "y2" once, as one object, e.g. "y2": {"color": ...}'),
])
def test_curve_crashes_are_errors_with_hints(spec, message, hint):
    assert error(core.normalize_spec, spec) == (message, hint)


@pytest.mark.parametrize("spec, message, hint", [
    ({**CHART, "legend": 5}, LEGEND, LEGEND_HINT),
    ({**CHART, "legend": ["upper right"]}, LEGEND, LEGEND_HINT),
    ({**CHART, "output": 5}, '"output" must be an object, got 5', 'e.g. "output": {"format": "png"}'),
    ({**CHART, "output": ["png"]}, "\"output\" must be an object, got ['png']", 'e.g. "output": {"format": "png"}'),
    ({**CHART, "output": "png", "format": "svg"}, "\"output\" is given twice: as 'png' and through \"format\"",
     'write "output" once, as one object, e.g. "output": {"format": ...}'),
    ({**CHART, "format": "svg", "output": None}, '"output" is given twice: as None and through "format"',
     'write "output" once, as one object, e.g. "output": {"format": ...}'),
    ({**CHART, "size": "6x4"}, "\"size\" must be [width, height] in inches, got '6x4'", 'e.g. "size": [6.4, 4.6]'),
    ({**CHART, "size": [7]}, '"size" must be [width, height] in inches, got [7]', 'e.g. "size": [6.4, 4.6]'),
    ({**CHART, "size": [0, 4]}, '"size" must be [width, height] in inches, got [0, 4]', 'e.g. "size": [6.4, 4.6]'),
    ({**CHART, "size": [6, "4in"]}, "\"size\" must be [width, height] in inches, got [6, '4in']", 'e.g. "size": [6.4, 4.6]'),
    ({**CHART, "dpi": "300dpi"}, "\"dpi\" must be a number of 1 or more, got '300dpi'", 'e.g. "dpi": 300'),
    ({**CHART, "dpi": float("inf")}, '"dpi" must be a number of 1 or more, got inf', 'e.g. "dpi": 300'),
    ({**CHART, "font_size": "big"}, "\"font_size\" must be a number above 0, got 'big'", 'e.g. "font_size": 11'),
    ({**CHART, "font_size": [11]}, '"font_size" must be a number above 0, got [11]', 'e.g. "font_size": 11'),
    ({**CHART, "point_size": "가동시간 (h)"}, "\"point_size\" must be a number above 0, got '가동시간 (h)'", POINT_HINT),
    ({**CHART, "marker_size": 0}, '"point_size" must be a number above 0, got 0', POINT_HINT),
    ({**CHART, "alpha": 1.5}, '"alpha" must be a number from 0 to 1, got 1.5', 'e.g. "alpha": 0.6 (1 = opaque)'),
    ({**CHART, "opacity": "half"}, "\"alpha\" must be a number from 0 to 1, got 'half'", 'e.g. "alpha": 0.6 (1 = opaque)'),
])
def test_chart_crashes_are_errors_with_hints(spec, message, hint):
    assert error(charts.normalize, spec) == (message, hint)


def test_numbers_as_text_still_work_for_charts():
    s = chart(size=["7", 3], dpi="150", font_size="12", point_size="30", alpha="0.5")
    assert (s["size"], s["dpi"], s["font_size"], s["point_size"], s["alpha"]) == ([7.0, 3.0], 150, 12.0, 30.0, 0.5)
    s = chart(dpi=150.7, font_size=None, alpha=0)
    assert (s["size"], s["dpi"], s["font_size"], s["alpha"]) == ([6.4, 4.6], 150, 11.0, 0.0)


def test_a_single_ask_is_a_list_and_not_done_reads_it():
    ask = {"ask": "3D", "how": "unsupported"}
    assert chart(asks=ask)["asks"] == [ask] and curve(asks=ask)["asks"] == [ask]
    assert core.not_done(chart(asks=ask)) == ["3D"]
    assert core.not_done({"asks": ask}) == ["3D"]
    assert core.not_done({"asks": 5}) == [] and core.not_done({"asks": "3D"}) == [] and core.not_done({}) == []
    assert core.not_done({"asks": [ask, {"ask": "x", "how": "key"}, "loose", {"how": "No"}]}) == ["3D", ""]


def test_the_callers_spec_is_not_changed():
    spec = {"file": "TGA.xlsx", "output": {"name": "n"}, "format": "pdf", "y": {"col": "C"}, "y1": {"color": "red"},
            "asks": [{"ask": "a", "how": "key"}]}
    before = copy.deepcopy(spec)
    s = core.normalize_spec(spec)
    assert spec == before
    assert (s["output"]["format"], s["output"]["name"], s["y1"]["col"], s["y1"]["color"]) == (["pdf"], "n", "C", "red")
    s["asks"].append("x")
    assert spec == before


@pytest.mark.parametrize("spec", [
    {**CHART, "format": "svg", "output": {"name": "n"}},
    {**CHART, "output": {"name": "n"}, "format": "svg"},
    {**CHART, "output": {"name": "n", "format": "png"}, "format": "svg"},
    {**CHART, "format": "svg", "output": {"name": "n", "format": "png"}},
])
def test_chart_format_goes_into_output_in_either_order(spec):
    assert charts.normalize(spec)["output"] == {"dir": None, "format": ["svg"], "name": "n"}


def test_chart_z_agg_is_checked_like_y_agg():
    assert error(charts.normalize, {**CHART, "chart": "heatmap", "y": "등급", "z": {"col": "수율", "agg": "bogus"}}) == (
        'unknown z.agg "bogus"', "use one of: " + ", ".join(charts.AGGS))
    assert chart(chart="heatmap", y="등급", z={"col": "수율", "agg": "평균"})["z"]["agg"] == "mean"


@pytest.mark.parametrize("legend", [{"where": "none"}, {"where": "None", "size": 9}, {"position": "없음"}, {"loc": "숨김"},
                                    {"where": " off ", "show": True}, "none", " Off ", "없음", False])
def test_chart_legend_none_hides_it_in_both_forms(legend):
    lg = chart(legend=legend)["legend"]
    assert (lg["where"], lg["show"]) == ("best", False)


def test_chart_axis_hint_has_no_internal_keys():
    message, hint = error(charts.normalize, {**CHART, "x": {"names": 1}})
    assert message == 'unknown key "x.names".'
    assert hint == ("allowed keys for x: agg, bins, col, date_format, flip, format, label, label_size, log, max, min, "
                    "order, period, rotate, step, tick_size")
    assert chart(y=[{"col": "수율", "label": "Yield"}])["y"] == {"col": ["수율"], "_names": {"수율": "Yield"}}


@pytest.mark.parametrize("text, value", [("1,000", 1000.0), ("12,345", 12345.0), ("1,000,000", 1e6), ("-1,000", -1000.0),
                                         (" 2,500 ", 2500.0), ("1,5", 1.5), ("0,125", 0.125), ("12,34", 12.34),
                                         ("1,0000", 1.0), ("800", 800.0)])
def test_thousands_separators_and_decimal_commas(text, value):
    assert core._num(text, "x.min") == value
    assert curve(x={"min": text})["x"]["min"] == value


def test_a_comma_and_a_point_together_are_not_a_number():
    assert error(core.normalize_spec, {**CURVE, "x": {"min": "1,000.5"}}) == (
        "x.min must be a number, got '1,000.5'", "write a plain number, e.g. 200")
