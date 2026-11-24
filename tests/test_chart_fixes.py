"""The chart fixes found by the TypeScript port: no float() crash on spec values, bins 1 / corr 1, aggregates of text,
bins with min and max, the pie legend, and missing category values. The TS port (ts/test/charts.test.ts) checks the
same cases."""
import json
from pathlib import Path

import pytest

import plotkit
from plotkit import api, charts
from plotkit.core import PlotkitError

INPUTS = Path(__file__).resolve().parent / "inputs"
M = "missing_values.csv"            # blanks in 날짜 (2), 일 (1), 그룹 (13), x값 (5), xu (1), y값 (9), g1 (1)


def live(spec):
    return plotkit.echarts_options(spec, INPUTS, full=True)


def model(spec):
    s = charts.normalize(api.with_base(spec, INPUTS))
    return s, charts.build_model(s, charts.load_frame(s))


def error(spec):
    with pytest.raises(PlotkitError) as e:
        live(spec)
    return e.value


# ------------------------------------------------------------ 1. point_size / alpha: no float() of a raw value
def test_layout_never_floats_a_raw_value():
    for key, bad in (("point_size", "가동시간 (h)"), ("alpha", [0.5])):
        s, m = model({"file": M, "chart": "scatter", "x": "x값", "y": "y값"})
        s[key] = bad                                   # as if normalize had let it through
        with pytest.raises(PlotkitError, match=f'"{key}" must be a number'):
            charts.layout(s, m)
    s, m = model({"file": M, "chart": "scatter", "x": "x값", "y": "y값", "point_size": 30, "alpha": 0.5})
    m = charts.layout(s, m)
    assert (m["point_size"], m["point_alpha"]) == (30.0, 0.5)
    e = error({"file": M, "chart": "line", "x": {"col": "x값", "rotate": "abc"}, "y": "y값"})
    assert e.message == "\"x.rotate\" must be a number, not 'abc'"


def test_alpha_zero_is_kept():
    r = live({"file": M, "chart": "scatter", "x": "x값", "y": "y값", "alpha": 0})
    assert r["options"][0]["series"][0]["itemStyle"]["opacity"] == 0.0
    assert live({"file": M, "chart": "scatter", "x": "x값", "y": "y값"})["options"][0]["series"][0]["itemStyle"]["opacity"] == 0.9


def test_point_size_from_a_column_is_refused():
    e = error({"file": M, "chart": "scatter", "x": "x값", "y": "y값", "point_size": "y2"})
    assert "point_size" in e.message


# ------------------------------------------------------------ 2. bins 1 is one bin; corr 1 is an error
def test_bins_one_is_one_bin():
    r = live({"file": M, "chart": "histogram", "x": "y값", "bins": 1})
    assert r["values"]["bins"] == 1
    assert live({"file": M, "chart": "histogram", "x": "y값", "bins": True})["values"]["bins"] == 7      # auto


def test_bins_count_must_be_one_or_more():
    e = error({"file": M, "chart": "histogram", "x": "y값", "bins": 0.5})
    assert e.message == '"bins" must be a number of bins (1 or more), not 0.5'


def test_corr_one_is_an_error():
    e = error({"file": M, "chart": "heatmap", "corr": 1})
    assert e.message == '"corr" must be a list of columns or "all", not 1' and '"all"' in e.hint
    assert live({"file": M, "chart": "heatmap", "corr": True})["values"]["cols"] == ["x값", "xu", "y값", "y2", "정수x"]
    e = error({"file": M, "chart": "heatmap", "corr": ["x값", "라벨"]})
    assert e.message == 'corr: "라벨" is not a numeric column'


# ------------------------------------------------------------ 3. aggregates of text
@pytest.mark.parametrize("how", ["mean", "sum", "median", "min", "max", "std"])
def test_text_aggregates_are_refused(how):
    for chart, extra in (("bar", {"y": {"col": "라벨", "agg": how}}), ("pie", {"y": {"col": "라벨", "agg": how}}),
                         ("heatmap", {"y": "g1", "z": {"col": "라벨", "agg": how}})):
        e = error({"file": M, "chart": chart, "x": "그룹", **extra})
        assert e.message == f'cannot take the {how} of "라벨": it holds text'
        assert e.hint == "use count or nunique, or a numeric column"


def test_dates_and_default_aggregates_are_refused_too():
    assert error({"file": M, "chart": "bar", "x": "그룹", "y": {"col": "날짜", "agg": "max"}}).message == \
        'cannot take the max of "날짜": it holds dates'
    assert error({"file": M, "chart": "bar", "x": "그룹", "y": "라벨"}).message == 'cannot take the mean of "라벨": it holds text'


def test_count_nunique_first_last_of_text_stay():
    r = live({"file": M, "chart": "bar", "x": "그룹", "y": {"col": "라벨", "agg": "nunique"}})
    assert r["values"]["series"]["라벨"] == [8.0, 5.0, 5.0]
    r = live({"file": M, "chart": "bar", "x": "그룹", "y": {"col": "라벨", "agg": "count"}})
    assert r["values"]["series"]["라벨"] == [19.0, 14.0, 14.0]
    r = live({"file": M, "chart": "bar", "x": "그룹", "y": {"col": "라벨", "agg": "first"}, "filter": "라벨 in [10, 2.5]"})
    assert r["values"]["series"]["라벨"] == [2.5, 10.0, 2.5]
    e = error({"file": M, "chart": "bar", "x": "그룹", "y": {"col": "라벨", "agg": "last"}})
    assert e.message == '"라벨" holds text, not numbers'


# ------------------------------------------------------------ 4. bins with min and max do not read the data
def test_bins_min_max_do_not_read_the_data():
    one_row = "y2 == 39.39"                           # the one row with y2 39.39 has no y값
    r = live({"file": M, "chart": "histogram", "x": "y값", "bins": {"width": 1, "min": 0, "max": 4}, "filter": one_row})
    assert r["values"] == {"bins": 4, "series": {"y값": {"n": 0, "mean": None}}}
    s, m = model({"file": M, "chart": "histogram", "x": "y값", "bins": {"width": 2, "min": 0, "max": 6}})
    assert m["edges"] == [0.0, 2.0, 4.0, 6.0]
    e = error({"file": M, "chart": "histogram", "x": "y값", "bins": {"width": 1}, "filter": one_row})
    assert (e.message, e.hint) == ("no numbers to bin", 'give "min" and "max" with the width, or check the filters')


def test_bad_bin_edges_are_errors():
    assert error({"file": M, "chart": "histogram", "x": "y값", "bins": [3, 1, 5]}).message == \
        '"bins" must be two or more increasing edges, not [3, 1, 5]'
    assert error({"file": M, "chart": "histogram", "x": "y값", "bins": {"closed": "right"}}).message == \
        '"bins" needs a "width" (or give a number of bins, or a list of edges)'


# ------------------------------------------------------------ 5. pie legend: no internal key, no entry without a series
def test_pie_legend_has_no_dummy():
    for extra in ({"by": "반응기"}, {"legend": {"where": "outside right", "title": "반응기"}}):
        spec = {"file": "run_log.csv", "chart": "pie", "x": "반응기", "legend": "outside right", **extra}
        opt = live(spec)["options"][0]
        assert "_legend_dummy" not in json.dumps(opt, ensure_ascii=False)
        assert opt["legend"]["data"] == [d["name"] for d in opt["series"][0]["data"]]
    bar = live({"file": "run_log.csv", "chart": "bar", "x": "등급", "y": "수율", "by": "반응기"})["options"][0]
    names = {s["name"] for s in bar["series"]}
    assert all((d["name"] if isinstance(d, dict) else d) in names for d in bar["legend"]["data"])     # the title too


# ------------------------------------------------------------ 6. missing category values are left out, with a note
@pytest.mark.parametrize("spec, note, used", [
    ({"chart": "bar", "x": "그룹", "y": "y값"}, "13 rows with no 그룹 left out", 47),
    ({"chart": "bar", "x": "g1", "y": "y값"}, "1 row with no g1 left out", 59),          # one row per x: no mean
    ({"chart": "line", "x": "xu", "y": "y값"}, "1 row with no xu left out", 59),
    ({"chart": "line", "x": "x값", "y": "y값"}, "5 rows with no x값 left out", 55),
    ({"chart": "bar", "x": "날짜", "y": "y값"}, "2 rows with no 날짜 left out", 58),
    ({"chart": "line", "x": {"col": "일", "period": "week"}, "y": "y2"}, "1 row with no 일 left out", 59),
    ({"chart": "pie", "x": "그룹"}, "13 rows with no 그룹 left out", 47),
    ({"chart": "heatmap", "x": "라벨", "y": "그룹"}, "13 rows with no 그룹 left out", 47),
    ({"chart": "scatter", "x": "x값", "y": "y2", "by": "그룹"}, "13 rows with no 그룹 left out", 47),
    ({"chart": "histogram", "x": "y2", "by": "그룹"}, "13 rows with no 그룹 left out", 47),
    ({"chart": "line", "x": {"col": "y2", "bins": [40, 50, 60]}, "y": "y값"}, "21 rows outside the bins of y2 left out", 39),
])
def test_missing_categories_are_left_out(spec, note, used):
    r = live({"file": M, **spec})
    assert r["warnings"][0] == note and r["rows_used"] == used and r["rows_total"] == 60
    text = json.dumps(r["values"], ensure_ascii=False)
    for bad in ('"None"', '"nan"', '"NaT"', "None–", "NaN"):
        assert bad not in text


def test_no_rows_left_after_leaving_out():
    e = error({"file": M, "chart": "bar", "x": "그룹", "y": "y2", "filter": "그룹 not in [A, B, C]"})
    assert e.message == "no rows left after leaving out the rows with no 그룹"
