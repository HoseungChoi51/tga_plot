"""The data_code sandbox: outputs come back without pickle, and no sandbox means no run unless the host allows it."""
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import plotkit
from plotkit import sandbox

HERE = Path(__file__).resolve().parent
LOG = str(HERE / "inputs" / "run_log.csv")
HAVE_BWRAP = shutil.which("bwrap") is not None


@pytest.fixture
def no_bwrap(monkeypatch):
    """As on Windows or macOS: bubblewrap is not there."""
    real = shutil.which
    monkeypatch.setattr(sandbox.shutil, "which", lambda name, *a, **k: None if name == "bwrap" else real(name, *a, **k))
    monkeypatch.delenv("PLOTKIT_NO_SANDBOX", raising=False)
    monkeypatch.delenv("PLOTKIT_ALLOW_UNSANDBOXED", raising=False)


@pytest.fixture
def plain(monkeypatch):
    """Run without bubblewrap, allowed (the tests check the transport, not bubblewrap)."""
    monkeypatch.setenv("PLOTKIT_NO_SANDBOX", "1")


def frame():
    df = pd.DataFrame({
        "반응기": ["R1", "R2", None, "R4"],
        "수율 (g/g)": [4.1, np.nan, 3.8, 4.3],
        "n": np.array([1, 2, 3, 4], dtype="int64"),
        "ok": [True, False, True, True],
        "날짜": pd.to_datetime(["2026-03-02", "2026-03-04", None, "2026-03-08"]),
        "시각": pd.to_datetime(["2026-03-02 09:00", "2026-03-02 10:00", "2026-03-02 11:00", "2026-03-02 12:00"]).tz_localize("Asia/Seoul"),
        "등급": pd.Categorical(["A", "B", "A", None], categories=["A", "B", "C"], ordered=True),
        "정지": pd.to_timedelta([30, 90, None, 15], unit="min"),
        "개수": pd.array([1, None, 3, 4], dtype="Int64"),
    })
    return df.iloc[[0, 1, 3]]                              # a filtered frame keeps its index labels


def test_frame_round_trip(plain):
    df = frame()
    out = sandbox.run("pass", {"df": df}, ["df"])["df"]
    pd.testing.assert_frame_equal(out, df, check_dtype=False)
    assert list(out.dtypes.astype(str)) == list(df.dtypes.astype(str))


def test_frame_changes_come_back(plain):
    df = frame()
    code = "df['수율'] = df['수율'] * 2\ndf = df.set_index('날짜')"      # '수율' finds '수율 (g/g)'
    out = sandbox.run(code, {"df": df}, ["df"])["df"]
    assert out.index.name == "날짜" and isinstance(out.index, pd.DatetimeIndex)
    assert out["수율 (g/g)"].tolist()[0] == pytest.approx(8.2)


def test_arrays_and_marks(plain):
    x = np.linspace(0, 10, 11)
    out = sandbox.run("y1 = y1 / y1.max()\nmarks.append({'x': np.float64(5), 'text': 'mid', 'v': float('nan')})",
                      {"x": x, "y1": x * 2, "y2": None, "sheet": "s", "marks": []}, ["x", "y1", "y2", "marks"])
    assert out["y1"].max() == 1.0 and out["y2"] is None
    assert out["marks"] == [{"x": 5.0, "text": "mid", "v": None}]


def test_a_pickled_output_is_not_loaded(plain):
    """Code that swaps np.save for a pickling writer: the host reads with allow_pickle=False and refuses."""
    code = ("import numpy as _n\n_save = _n.save\n"
            "def _evil(f, a, allow_pickle=False):\n    _save(f, _n.array([{'boom': 1}], dtype=object), allow_pickle=True)\n"
            "_n.save = _evil\ny1 = y1 + 1")
    with pytest.raises(plotkit.PlotkitError, match="cannot be read back"):
        sandbox.run(code, {"x": np.arange(3.0), "y1": np.arange(3.0), "y2": None, "sheet": "s", "marks": []},
                    ["x", "y1", "y2", "marks"])


def test_no_sandbox_means_refused(no_bwrap):
    assert sandbox.mode() == "refused"
    with pytest.raises(plotkit.PlotkitError) as e:
        sandbox.run("df['k'] = 1", {"df": frame()}, ["df"])
    assert "bubblewrap" in e.value.message and "allow_unsandboxed" in e.value.hint


def test_the_host_can_allow_it(no_bwrap):
    with sandbox.policy(allow_unsandboxed=True):
        assert sandbox.mode() == "plain"
        out = sandbox.run("df['k'] = 1", {"df": frame()}, ["df"])["df"]
    assert out["k"].tolist() == [1, 1, 1]
    assert sandbox.mode() == "refused"                     # only inside the with block


def test_env_switches(no_bwrap, monkeypatch):
    monkeypatch.setenv("PLOTKIT_ALLOW_UNSANDBOXED", "1")
    assert sandbox.mode() == "plain"
    monkeypatch.delenv("PLOTKIT_ALLOW_UNSANDBOXED")
    monkeypatch.setenv("PLOTKIT_NO_SANDBOX", "1")             # the host has its own sandbox
    assert sandbox.mode() == "plain"


def test_refused_data_code_reaches_the_model_as_error_and_hint(no_bwrap, tmp_path):
    spec = {"file": LOG, "chart": "bar", "x": "반응기", "y": "수율", "data_code": "df['수율'] = df['수율'] * 100"}
    with pytest.raises(plotkit.PlotkitError) as e:
        plotkit.plot(spec, engine="matplotlib", out_dir=tmp_path)
    assert "no data_code" in e.value.hint


@pytest.mark.skipif(not HAVE_BWRAP, reason="bubblewrap is not installed")
def test_bubblewrap_has_no_network():
    """Only the loopback interface exists inside (checked locally; nothing is sent anywhere)."""
    code = "import socket\nnet = sorted(n for _, n in socket.if_nameindex())"
    assert sandbox.run(code, {"net": None}, ["net"])["net"] == ["lo"]


@pytest.mark.parametrize("engine", ["matplotlib", "echarts"])
def test_chart_with_data_code(engine, tmp_path, plain):
    spec = {"file": LOG, "chart": "bar", "x": "반응기", "y": {"col": "수율 %", "agg": "mean"},
            "data_code": "df['수율 %'] = df['수율'] * 10"}
    r = plotkit.plot(spec, engine=engine, out_dir=tmp_path)
    assert r["ok"] and max(v for v in r["values"]["series"]["수율 %"] if v is not None) > 40


@pytest.mark.skipif(not HAVE_BWRAP, reason="bubblewrap is not installed")
def test_round_trip_in_bubblewrap(monkeypatch):
    monkeypatch.delenv("PLOTKIT_NO_SANDBOX", raising=False)
    assert sandbox.mode() == "bwrap"
    df = frame()
    out = sandbox.run("df['k'] = df['n'] * 2", {"df": df}, ["df"])["df"]
    pd.testing.assert_frame_equal(out.drop(columns="k"), df, check_dtype=False)
    assert out["k"].tolist() == [2, 4, 8]


def test_a_python_under_tmp_stays_visible(monkeypatch):
    """/tmp is an empty tmpfs inside bubblewrap; a venv or a PyInstaller build there is bound back, read-only."""
    monkeypatch.setattr(sandbox.sys, "prefix", "/tmp/somewhere/venv")
    binds = sandbox._python_binds()
    assert binds[:3] == ["--ro-bind", "/tmp/somewhere/venv", "/tmp/somewhere/venv"]
