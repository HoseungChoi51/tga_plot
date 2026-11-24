"""ECharts is the default engine and needs no matplotlib; the colour and tick ports equal matplotlib's."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import plotkit
from conftest import needs_mpl
from plotkit import colors, ticks

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "tests" / "inputs"

NO_MPL = r"""
import sys
for m in ("matplotlib", "matplotlib.pyplot", "matplotlib.colors", "matplotlib.ticker"):
    sys.modules[m] = None                                  # as if it were not installed
import json, tempfile, plotkit
base, out = sys.argv[1], tempfile.mkdtemp()
specs = [{"file": "TGA.xlsx", "sheets": "all", "combine": True, "colors": ["navy", "tab:orange", "C2"]},
         {"file": "TGA.xlsx", "sheets": 1, "annotate": {"b": {"type": "band", "x_min": 300, "x_max": 450, "color": "빨강"}}},
         {"file": "run_log.csv", "chart": "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"}, "colors": {"R1": "0.5"}},
         {"file": "run_log.csv", "chart": "heatmap", "x": "반응기", "y": "등급", "z": {"col": "수율", "agg": "mean"},
          "values": True, "cmap": "YlOrRd"},
         {"file": "run_log.csv", "chart": "histogram", "x": "수율"},
         {"file": "run_log.csv", "chart": "scatter", "x": "구역2 온도", "y": "수율", "trend": True}]
res = []
for s in specs:
    plotkit.validate(s, base)
    o = plotkit.echarts_options(s, base, full=True)
    r = plotkit.render(s, out, formats=("png", "svg"), base=base)
    res.append([o["kind"], len(o["options"]), len(r["saved"])])
try:
    plotkit.render(specs[0], out, engine="matplotlib", base=base)
    res.append("matplotlib drew")
except plotkit.PlotkitError as e:
    res.append(e.hint)
res.append(any(v is not None for k, v in sys.modules.items() if k.startswith("matplotlib")))
print(json.dumps(res, ensure_ascii=False))
"""


def test_echarts_needs_no_matplotlib():
    p = subprocess.run([sys.executable, "-c", NO_MPL, str(INPUTS)], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-2000:]
    res = json.loads(p.stdout.strip().splitlines()[-1])
    assert res[:6] == [["curve", 1, 2], ["curve", 1, 2], ["chart", 1, 2], ["chart", 1, 2], ["chart", 1, 2], ["chart", 1, 2]]
    assert "plotkit[matplotlib]" in res[6]                 # the optional engine says how to get it
    assert res[7] is False                                 # and matplotlib was never imported


def test_echarts_is_the_default(monkeypatch):
    monkeypatch.delenv("PLOTKIT_ENGINE", raising=False)
    assert plotkit.engine_name() == "echarts"


def test_unknown_cmap_lists_the_built_in_ones():
    with pytest.raises(plotkit.PlotkitError) as e:
        plotkit.echarts_options({"file": "run_log.csv", "chart": "heatmap", "x": "반응기", "y": "등급",
                                 "cmap": "no_such_map"}, INPUTS)
    assert "viridis" in e.value.hint and "YlOrRd" in e.value.hint


# =================================================================== the ports equal matplotlib
@needs_mpl
def test_ticks_equal_matplotlib():
    from matplotlib.ticker import MaxNLocator
    rng = np.random.default_rng(0)
    for _ in range(3000):
        a = rng.choice([1e-6, 1e-3, 1, 10, 100, 1e4, 1e7]) * rng.normal()
        w = abs(rng.choice([1e-9, 1e-4, 0.1, 1, 50, 1e3, 1e6]) * rng.random())
        for nb in ("auto", 4, 6, 7, 10):
            want = MaxNLocator(nbins=nb, steps=list(ticks.STEPS)).tick_values(a, a + w)
            assert np.array_equal(ticks.tick_values(a, a + w, nb), want), (a, w, nb)


@needs_mpl
def test_colours_equal_matplotlib():
    from matplotlib import colors as mc
    specs = list(mc._colors_full_map) + ["C0", "C9", "C12", "0.5", "1", "#abc", "#aabbcc", "#aabbccdd", "#abcd", "none",
                                         "Red", "NAVY", "nope", "#12", "1.5", "", "R", "빨강"]
    for c in specs:
        assert colors.is_color_like(c) == mc.is_color_like(c), c
        if mc.is_color_like(c):
            assert colors.to_hex(c) == mc.to_hex(c) and colors.to_rgb(c) == mc.to_rgb(c), c


@needs_mpl
def test_colormaps_equal_matplotlib():
    import matplotlib
    from matplotlib.colors import to_hex
    for name in colors.colormap_names():
        cm, m = colors.colormap(name), matplotlib.colormaps[name]
        for t in list(np.linspace(0, 1, 513)) + [-0.2, 1.3]:
            r, g, b, _ = m(t)
            assert cm.hex(t) == to_hex(m(t)) and cm.dark(t) == (0.299 * r + 0.587 * g + 0.114 * b < 0.5), (name, t)


@needs_mpl
def test_colour_data_is_current():
    """data/colors.json is what python -m plotkit.colors --generate writes for the installed matplotlib."""
    import matplotlib
    d = json.loads(colors.DATA.read_text(encoding="utf-8"))
    if d["matplotlib"] != matplotlib.__version__:
        pytest.skip(f"data from matplotlib {d['matplotlib']}, installed {matplotlib.__version__}")
    assert colors.DATA.read_text(encoding="utf-8") == colors.dumps(colors.generate())
