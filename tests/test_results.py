"""The router, the shared result shape and the host's control over files (offline)."""
from pathlib import Path

import pytest

import plotkit
from plotkit import charts, core

HERE = Path(__file__).resolve().parent
TGA = str(HERE / "inputs" / "TGA.xlsx")
LOG = str(HERE / "inputs" / "run_log.csv")
SHARED = {"ok", "kind", "engine", "saved", "warnings", "not_done", "values"}
ENGINES = ["matplotlib", "echarts"]


@pytest.mark.parametrize("key", sorted(charts.CHART_KEYS))
def test_every_chart_alias_routes_to_charts(key, tmp_path):
    r = plotkit.plot({"file": LOG, key: "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"}},
                     engine="matplotlib", out_dir=tmp_path)
    assert r["ok"] and r["kind"] == "chart" and r["chart"] == "bar"


def test_curve_keys_still_go_to_curves(tmp_path):
    r = plotkit.plot({"file": TGA, "sheets": 1}, engine="matplotlib", out_dir=tmp_path)
    assert r["kind"] == "curve"


@pytest.mark.parametrize("engine", ENGINES)
def test_one_result_shape(engine, tmp_path):
    asks = [{"ask": "x축 200 간격", "how": "key"}, {"ask": "박스 플롯", "how": "unsupported"}, {"ask": "inset", "how": "none"}]
    c = plotkit.plot({"file": TGA, "sheets": 1, "asks": asks}, engine=engine, out_dir=tmp_path / "c")
    t = plotkit.plot({"file": LOG, "chart": "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"}, "asks": asks},
                     engine=engine, out_dir=tmp_path / "t")
    for r in (c, t):
        assert SHARED <= set(r), SHARED - set(r)
        assert r["engine"] == engine
        assert r["not_done"] == ["박스 플롯", "inset"]          # one rule for both paths
        assert r["saved"] and all(Path(p).exists() for p in r["saved"])
    assert c["saved"] == [p for x in c["plots"] for p in x["saved"]]
    sheet = c["plots"][0]["sheet"]
    assert {"residue", "peak"} <= set(c["values"][sheet])
    assert {"bar"} == {t["chart"]} and set(t["values"]["categories"]) == {"R1", "R2", "R3", "R4"}


@pytest.mark.parametrize("engine", ENGINES)
def test_host_folder_and_formats_win(engine, tmp_path):
    spec = {"file": TGA, "sheets": 1, "output": {"dir": str(tmp_path / "model_dir"), "format": "pdf"}}
    r = plotkit.plot(spec, engine=engine, out_dir=tmp_path / "host", formats=["svg"], summary_csv=False)
    assert [Path(p).suffix for p in r["saved"]] == [".svg"]
    assert all(Path(p).parent == tmp_path / "host" for p in r["saved"])
    assert not (tmp_path / "model_dir").exists()
    assert not (tmp_path / "host" / "summary.csv").exists()


def test_summary_csv_kept_by_default(tmp_path):
    plotkit.plot({"file": TGA, "sheets": 1}, engine="matplotlib", out_dir=tmp_path)
    assert (tmp_path / "summary.csv").exists()


def test_bad_format_from_the_host_is_an_error(tmp_path):
    with pytest.raises(plotkit.PlotkitError):
        plotkit.plot({"file": TGA, "sheets": 1}, engine="matplotlib", out_dir=tmp_path, formats=["bmp"])


def test_not_done_is_shared():
    assert core.not_done({"asks": [{"ask": "a", "how": "Unsupported"}, {"ask": "b", "how": "key"}, "loose text"]}) == ["a"]
