"""Colours without matplotlib: names, hex codes and colormaps, as matplotlib reads them.

The ECharts engine needs to check and convert colours ("navy", "빨강" via core.KOREAN_COLORS, "#c0392b", "tab:blue",
"0.5" grey, "C3") and to colour heatmaps. matplotlib is optional (the matplotlib engine), so this module ports the
parts of matplotlib.colors plotkit uses and reads matplotlib's tables from data/colors.json: every colour name, the
default colour cycle, and the 256-level lookup table of the common colormaps (with the black/white label choice per
level). The port follows matplotlib (BSD-compatible licence); tests/test_engines.py checks it against matplotlib.

    python -m plotkit.colors --generate     # rewrite data/colors.json from the installed matplotlib
"""
import json
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "colors.json"
_NTH = re.compile(r"\AC[0-9]+\Z")

# colormaps kept in data/colors.json (each also reversed, name_r); others need matplotlib
CMAPS = ("viridis", "plasma", "inferno", "magma", "cividis", "turbo", "Blues", "Reds", "Greens", "Greys", "Oranges",
         "Purples", "YlOrRd", "YlOrBr", "YlGnBu", "YlGn", "PuBu", "BuGn", "RdBu", "RdYlBu", "RdYlGn", "Spectral",
         "PiYG", "coolwarm", "bwr", "seismic", "gray", "binary", "hot", "jet")


@lru_cache(maxsize=None)
def _data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def to_rgba(c):
    """(r, g, b, a) floats in 0..1 for a colour as matplotlib reads it; raises ValueError when it is not one."""
    d = _data()
    if isinstance(c, str) and _NTH.match(c):
        cyc = d["cycle"]
        c = cyc[int(c[1:]) % len(cyc)]
    orig = c
    if isinstance(c, str):
        if c.lower() == "none":
            return (0.0, 0.0, 0.0, 0.0)
        names = d["names"]
        if c in names:
            c = names[c]
        elif len(c) != 1 and c.lower() in names:
            c = names[c.lower()]
    if isinstance(c, str):
        if re.fullmatch("#[a-fA-F0-9]+", c):
            h = c[1:]
            if len(h) == 6:
                return (*[n / 0xff for n in bytes.fromhex(h)], 1.0)
            if len(h) == 3:
                return (*[int(n, 16) / 0xf for n in h], 1.0)
            if len(h) == 8:
                return tuple(n / 0xff for n in bytes.fromhex(h))
            if len(h) == 4:
                return tuple(int(n, 16) / 0xf for n in h)
            raise ValueError(f"Invalid hex color specifier: {orig!r}")
        try:
            g = float(c)
        except ValueError:
            raise ValueError(f"Invalid RGBA argument: {orig!r}")
        if not 0 <= g <= 1:
            raise ValueError(f"Invalid string grayscale value {orig!r}")
        return (g, g, g, 1.0)
    if isinstance(c, (list, tuple)) and len(c) in (3, 4) and all(isinstance(x, (int, float)) for x in c):
        c = tuple(float(x) for x in c) + ((1.0,) if len(c) == 3 else ())
        if any(x < 0 or x > 1 for x in c):
            raise ValueError("RGBA values should be within 0-1 range")
        return c
    raise ValueError(f"Invalid RGBA argument: {orig!r}")


def is_color_like(c):
    try:
        to_rgba(c)
    except (TypeError, ValueError):
        return False
    return True


def to_rgb(c):
    return to_rgba(c)[:3]


def to_hex(c):
    """#rrggbb, rounded like matplotlib.colors.to_hex."""
    return "#" + "".join(format(round(v * 255), "02x") for v in to_rgb(c))


class Colormap:
    """A colormap as 256 levels: colormap(t) picks the level the way matplotlib does for t in 0..1."""

    def __init__(self, name, lut, dark):
        self.name, self.lut, self._dark = name, lut, dark
        self.N = len(lut)

    def _level(self, t):
        x = t * self.N
        if x == self.N:
            x = self.N - 1
        if x < 0:
            return 0
        return min(int(x), self.N - 1)

    def hex(self, t):
        """The colour at t (0..1) as #rrggbb."""
        return self.lut[self._level(t)]

    def dark(self, t):
        """True when a label on the colour at t should be white (luminance below one half, from matplotlib's floats)."""
        return self._dark[self._level(t)] == "1"


def colormap(name):
    """The colormap named name (matplotlib's names). The common ones are built in; others need matplotlib.
    Raises KeyError for an unknown name."""
    maps = _data()["cmaps"]
    if name in maps:
        lut, dark = maps[name]
        return Colormap(name, [f"#{lut[i:i + 6]}" for i in range(0, len(lut), 6)], dark)
    try:
        import matplotlib
    except ImportError:
        raise KeyError(name)
    lut, dark = _from_matplotlib(matplotlib.colormaps[name])
    return Colormap(name, [f"#{lut[i:i + 6]}" for i in range(0, len(lut), 6)], dark)


def colormap_names():
    return sorted(_data()["cmaps"])


# =================================================================== generating data/colors.json
def _from_matplotlib(cm):
    import numpy as np
    from matplotlib.colors import to_hex as mpl_hex
    rgba = cm(np.arange(cm.N) / cm.N + 0.5 / cm.N)         # the centre of each level: exactly level i
    lut = "".join(mpl_hex(c)[1:] for c in rgba)
    dark = "".join("1" if 0.299 * r + 0.587 * g + 0.114 * b < 0.5 else "0" for r, g, b, _ in rgba)
    return lut, dark


def generate():
    import matplotlib
    from matplotlib import colors as mc
    names = {}
    for k, v in mc._colors_full_map.items():
        if isinstance(k, str):
            names[k] = v if isinstance(v, str) else [float(x) for x in v]
    cycle = matplotlib.rcParamsDefault["axes.prop_cycle"].by_key()["color"]
    cmaps = {}
    for n in CMAPS:
        for name in (n, n + "_r"):
            cmaps[name] = _from_matplotlib(matplotlib.colormaps[name])
    return {"matplotlib": matplotlib.__version__, "names": dict(sorted(names.items())), "cycle": cycle,
            "cmaps": cmaps}


def dumps(d):
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n"


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--generate"]:
        DATA.parent.mkdir(exist_ok=True)
        DATA.write_text(dumps(generate()), encoding="utf-8")
        print(f"wrote {DATA}")
    else:
        print(__doc__)
