"""Figure facts: what a plot actually shows, in one JSON shape for matplotlib and ECharts.

The evaluation scores every arm (plotkit specs and raw model-written code) on these facts, never on the
spec, so the arms are judged the same way.

    facts = {"engine", "size_in", "dpi", "title": {text,size,color}, "panels": [panel, ...],
             "texts": [...], "legend": {...}, "files": [{path, format, px}]}
    panel = {"x": axis, "y1": axis, "y2": axis | None, "lines": [...], "spans": [...], "vlines": [...],
             "hlines": [...], "fills": int, "grid": bool}
    axis  = {"min","max","scale","inverted","ticks","step","label","label_size","label_color",
             "tick_size","tick_color","tick_direction","minor"}
    line  = {"axis","kind" (line|scatter),"color","width","style","marker","n","x_range","y_range","label"}
    text  = {"text","x","y","axis","color","size","panel"}   (x/y in data units when known)
Sizes are in points, colours are "#rrggbb".
"""
import atexit
import json
import os
import re
import struct
from pathlib import Path

import numpy as np

PT = 96 / 72                      # ECharts px per point (plotkit lays the SVG out at 96 px per inch)


# =================================================================== small helpers
def hexcolor(c):
    """Any matplotlib colour, CSS rgb()/rgba() string or ECharts colour -> '#rrggbb' (None if unknown)."""
    if c is None:
        return None
    from matplotlib.colors import to_hex
    if isinstance(c, str):
        m = re.fullmatch(r"\s*rgba?\(([^)]*)\)\s*", c)
        if m:
            p = [float(v) for v in m.group(1).split(",")[:3]]
            return to_hex([v / 255 for v in p])
        if isinstance(c, str) and c.strip().lower() in ("none", "transparent", "inherit", "auto"):
            return None
    if isinstance(c, dict):                     # ECharts gradient
        stops = c.get("colorStops") or []
        return hexcolor(stops[0].get("color")) if stops else None
    try:
        return to_hex(c)
    except (ValueError, TypeError):
        return None


def png_px(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return list(struct.unpack(">II", head[16:24]))
    except OSError:
        pass
    return None


def file_entry(path, fmt=None):
    p = Path(path)
    fmt = (fmt or p.suffix.lstrip(".")).lower().replace("jpeg", "jpg").replace("tiff", "tif")
    return {"path": str(p), "format": fmt, "px": png_px(p) if fmt == "png" else None,
            "exists": p.exists() and p.stat().st_size > 0}


def tick_step(ticks, lo, hi, log=False):
    """The spacing of evenly spaced ticks inside [lo, hi] (None for log axes or fewer than 3 ticks)."""
    if log or not ticks:
        return None
    span = abs(hi - lo) or 1.0
    t = sorted(v for v in ticks if min(lo, hi) - 1e-9 * span <= v <= max(lo, hi) + 1e-9 * span)
    if len(t) < 3:
        return None
    d = np.diff(t)
    inner = d[1:-1] if len(d) > 2 else d          # ECharts puts the axis ends among the ticks
    step = float(np.median(inner))
    return round(step, 10) if step > 0 else None


def _rng(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    return [float(a.min()), float(a.max())] if a.size else None


def _style(ls):
    if ls in (None, "None", "none", " ", ""):
        return "none"
    return {"-": "solid", "solid": "solid", "--": "dashed", "dashed": "dashed", ":": "dotted",
            "dotted": "dotted", "-.": "dashdot", "dashdot": "dashdot"}.get(ls, "dashed")


def _where(cx, cy, box):
    """'upper right' etc. for a point in a box given as (x0, y0, x1, y1) with y growing upwards."""
    x0, y0, x1, y1 = box
    fx = (cx - x0) / ((x1 - x0) or 1)
    fy = (cy - y0) / ((y1 - y0) or 1)
    h = "left" if fx < 1 / 3 else "right" if fx > 2 / 3 else "center"
    v = "lower" if fy < 1 / 3 else "upper" if fy > 2 / 3 else "center"
    return "center" if h == v == "center" else f"{v} {h}" if v != "center" else f"center {h}" if h != "center" else f"{v} center"


# =================================================================== matplotlib
def _mpl_axis(ax, which, twin=None):
    a = ax.xaxis if which == "x" else ax.yaxis
    lo, hi = ax.get_xlim() if which == "x" else ax.get_ylim()
    scale = ax.get_xscale() if which == "x" else ax.get_yscale()
    ticks = [float(v) for v in a.get_majorticklocs()]
    ticks = [v for v in ticks if min(lo, hi) - 1e-9 <= v <= max(lo, hi) + 1e-9]
    labels = [t for t in a.get_ticklabels() if t.get_text()]
    lab0 = labels[0] if labels else None
    try:
        tickdir = a.majorTicks[0]._tickdir
    except (AttributeError, IndexError):
        tickdir = None
    minor = [v for v in a.get_minorticklocs() if min(lo, hi) <= v <= max(lo, hi)]
    minor_visible = bool(minor) and bool(a.get_minor_ticks()) and a.get_minor_ticks()[0].tick1line.get_visible()
    return {"min": float(min(lo, hi)), "max": float(max(lo, hi)), "scale": scale,
            "inverted": bool(lo > hi), "ticks": ticks, "step": tick_step(ticks, lo, hi, scale == "log"),
            "label": a.label.get_text(), "label_size": float(a.label.get_fontsize()),
            "label_color": hexcolor(a.label.get_color()),
            "tick_size": float(lab0.get_fontsize()) if lab0 else None,
            "tick_color": hexcolor(lab0.get_color()) if lab0 else None,
            "tick_direction": tickdir, "minor": int(minor_visible and len(minor))}


def _is_data_line(line):
    x, y = line.get_xdata(orig=False), line.get_ydata(orig=False)
    return np.size(x) >= 5 and np.size(y) >= 5


def mpl_figure_facts(fig):
    """Facts of a drawn matplotlib Figure (call after savefig so texts and ticks are laid out)."""
    from matplotlib.collections import PathCollection, PolyCollection
    from matplotlib.patches import Polygon, Rectangle
    from matplotlib.text import Annotation
    renderer = fig.canvas.get_renderer()
    axes = [a for a in fig.axes if a.get_visible() and a.axison]
    groups = []                                   # axes sharing one box = one panel (twinx)
    for a in axes:
        box = tuple(np.round(a.get_position().bounds, 3))
        for g in groups:
            if g["box"] == box:
                g["axes"].append(a)
                break
        else:
            groups.append({"box": box, "axes": [a]})
    groups.sort(key=lambda g: (-round(g["box"][1] + g["box"][3], 2), g["box"][0]))   # top to bottom, left to right
    panels, texts = [], []

    def text_entry(t, ax, axis_name, pi):
        s = t.get_text()
        if not s or not s.strip() or not t.get_visible():
            return None
        try:                                   # clipped annotations stay in ax.texts but are not drawn
            if isinstance(t, Annotation) and not t._check_xy(renderer):
                return None
        except Exception:
            pass
        x = y = None
        try:
            if isinstance(t, Annotation) and t.xycoords == "data":
                x, y = t.xy
            else:
                disp = t.get_transform().transform(t.get_position())
                x, y = ax.transData.inverted().transform(disp)
        except Exception:
            pass
        return {"text": s, "x": None if x is None else float(x), "y": None if y is None else float(y),
                "axis": axis_name, "color": hexcolor(t.get_color()), "size": float(t.get_fontsize()), "panel": pi}

    for pi, g in enumerate(groups):
        prim = g["axes"][0]
        twin = None
        for a in g["axes"][1:]:
            if a.yaxis.get_ticks_position() in ("right",) or a.yaxis.get_label_position() == "right":
                twin = a
        if twin is None and len(g["axes"]) > 1:
            twin = g["axes"][1]
        panel = {"x": _mpl_axis(prim, "x"), "y1": _mpl_axis(prim, "y"),
                 "y2": _mpl_axis(twin, "y") if twin is not None else None,
                 "lines": [], "spans": [], "vlines": [], "hlines": [], "fills": 0,
                 "grid": any(gl.get_visible() for gl in prim.xaxis.get_gridlines() + prim.yaxis.get_gridlines()),
                 "title": prim.get_title() or prim.get_title("left") or prim.get_title("right")}
        abox = prim.get_window_extent(renderer)
        for ax, name in ((prim, "y1"), (twin, "y2")):
            if ax is None:
                continue
            for ln in ax.get_lines():
                if not ln.get_visible():
                    continue
                xd = np.asarray(ln.get_xdata(orig=False), dtype=float)
                yd = np.asarray(ln.get_ydata(orig=False), dtype=float)
                if _is_data_line(ln):
                    marker = ln.get_marker() not in (None, "None", "", " ", "none")
                    style = _style(ln.get_linestyle())
                    panel["lines"].append({"axis": name, "kind": "scatter" if style == "none" else "line",
                                           "color": hexcolor(ln.get_color()), "width": float(ln.get_linewidth()),
                                           "style": style, "marker": marker, "n": int(xd.size),
                                           "x_range": _rng(xd), "y_range": _rng(yd),
                                           "label": "" if ln.get_label().startswith("_") else ln.get_label()})
                elif xd.size == 2 and xd[0] == xd[1] and yd[0] != yd[1]:
                    panel["vlines"].append({"x": float(xd[0]), "color": hexcolor(ln.get_color()),
                                            "style": _style(ln.get_linestyle())})
                elif yd.size == 2 and yd[0] == yd[1] and xd[0] != xd[1]:
                    panel["hlines"].append({"y": float(yd[0]), "axis": name, "color": hexcolor(ln.get_color()),
                                            "style": _style(ln.get_linestyle())})
            for c in ax.collections:
                if not c.get_visible():
                    continue
                if isinstance(c, PathCollection):
                    off = c.get_offsets()
                    if len(off) >= 5:
                        fc = c.get_facecolor()
                        panel["lines"].append({"axis": name, "kind": "scatter",
                                               "color": hexcolor(fc[0]) if len(fc) else None,
                                               "width": 0.0, "style": "none", "marker": True, "n": int(len(off)),
                                               "x_range": _rng(off[:, 0]), "y_range": _rng(off[:, 1]),
                                               "label": "" if str(c.get_label()).startswith("_") else str(c.get_label())})
                elif isinstance(c, PolyCollection):
                    bb = c.get_window_extent(renderer)
                    if bb.height >= 0.9 * abox.height and bb.width < 0.98 * abox.width:   # axvspan-like
                        x0, x1 = ax.transData.inverted().transform([[bb.x0, 0], [bb.x1, 0]])[:, 0]
                        panel["spans"].append({"x_min": float(x0), "x_max": float(x1),
                                               "color": hexcolor(c.get_facecolor()[0]) if len(c.get_facecolor()) else None})
                    else:
                        panel["fills"] += 1
            for p in ax.patches:
                if not p.get_visible() or not isinstance(p, (Rectangle, Polygon)):
                    continue
                bb = p.get_window_extent(renderer)
                if bb.height >= 0.9 * abox.height and bb.width < 0.98 * abox.width:
                    x0, x1 = ax.transData.inverted().transform([[bb.x0, 0], [bb.x1, 0]])[:, 0]
                    panel["spans"].append({"x_min": float(min(x0, x1)), "x_max": float(max(x0, x1)),
                                           "color": hexcolor(p.get_facecolor()), "alpha": p.get_alpha()})
            for t in ax.texts:
                e = text_entry(t, ax, name, pi)
                if e:
                    texts.append(e)
        panels.append(panel)

    for t in fig.texts:
        if t.get_text().strip() and t.get_visible():
            texts.append({"text": t.get_text(), "x": None, "y": None, "axis": None,
                          "color": hexcolor(t.get_color()), "size": float(t.get_fontsize()), "panel": None})

    title = None
    sup = getattr(fig, "_suptitle", None)
    for g in groups:
        for t in (g["axes"][0].title, g["axes"][0]._left_title, g["axes"][0]._right_title):
            if t.get_text().strip():
                title = {"text": t.get_text(), "size": float(t.get_fontsize()), "color": hexcolor(t.get_color())}
                break
        if title:
            break
    if sup is not None and sup.get_text().strip():
        title = {"text": sup.get_text(), "size": float(sup.get_fontsize()), "color": hexcolor(sup.get_color())}

    legend = {"shown": False, "entries": [], "size": None, "inside": None, "where": None}
    legs = [a.get_legend() for a in axes if a.get_legend() is not None] + list(fig.legends)
    for lg in legs:
        if not lg.get_visible():
            continue
        entries = [t.get_text() for t in lg.get_texts() if t.get_text()]
        if not entries:
            continue
        bb = lg.get_window_extent(renderer)
        host = groups[0]["axes"][0].get_window_extent(renderer) if groups else bb
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        inside = host.x0 - 2 <= cx <= host.x1 + 2 and host.y0 - 2 <= cy <= host.y1 + 2
        legend = {"shown": True, "entries": legend["entries"] + entries,
                  "size": float(lg.get_texts()[0].get_fontsize()), "inside": bool(inside),
                  "where": _where(cx, cy, (host.x0, host.y0, host.x1, host.y1)) if inside else "outside",
                  "colors": [hexcolor(t.get_color()) for t in lg.get_texts()]}
    return {"engine": "matplotlib", "size_in": [float(v) for v in fig.get_size_inches()],
            "dpi": None, "title": title, "panels": panels, "texts": texts, "legend": legend, "files": []}


_HOOK = {"installed": False, "facts": {}, "order": [], "out": None}


def install_mpl_hook(out_path=None):
    """Record facts of every Figure saved from now on (also when saved twice, e.g. png + pdf).

    out_path: also write {"figures": [...]} there at every save and at exit."""
    from matplotlib.figure import Figure
    _HOOK["out"] = out_path
    if _HOOK["installed"]:
        return _HOOK
    orig = Figure.savefig

    def savefig(self, fname, *args, **kw):
        res = orig(self, fname, *args, **kw)
        try:
            key = id(self)
            if key not in _HOOK["facts"]:
                f = mpl_figure_facts(self)
                _HOOK["facts"][key] = f
                _HOOK["order"].append(key)
            f = _HOOK["facts"][key]
            dpi = kw.get("dpi")
            if dpi in (None, "figure"):
                import matplotlib
                d = matplotlib.rcParams.get("savefig.dpi", "figure")
                dpi = self.dpi if d == "figure" else d
            f["dpi"] = float(dpi)
            if isinstance(fname, (str, os.PathLike)):
                f["files"].append(file_entry(fname, kw.get("format")))
            if _HOOK["out"]:
                dump_mpl_hook(_HOOK["out"])
        except Exception as e:                    # facts must never break the plot itself
            _HOOK.setdefault("errors", []).append(repr(e))
        return res

    Figure.savefig = savefig
    _HOOK["installed"] = True
    if out_path:
        atexit.register(lambda: dump_mpl_hook(_HOOK["out"]))
    return _HOOK


def take_mpl_facts():
    """Facts recorded since the last call (and forget them)."""
    out = [_HOOK["facts"][k] for k in _HOOK["order"]]
    _HOOK["facts"].clear()
    _HOOK["order"].clear()
    return out


def dump_mpl_hook(path):
    if not path:
        return
    figs = [_HOOK["facts"][k] for k in _HOOK["order"]]
    for f in figs:                               # file sizes are known only after writing
        for e in f["files"]:
            e.update(file_entry(e["path"], e["format"]))
    Path(path).write_text(json.dumps({"figures": figs, "errors": _HOOK.get("errors", [])}, ensure_ascii=False),
                          encoding="utf-8")


# =================================================================== ECharts
ECHARTS_PALETTE = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc"]


def _as_list(v):
    return v if isinstance(v, list) else [] if v is None else [v]


def _num(v):
    try:
        f = float(v)
        return f if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _dash_array(d):
    """ECharts dash arrays (as plotkit writes them) -> solid/dashed/dotted/dashdot."""
    d = [float(v) for v in d if _num(v) is not None]
    if len(d) >= 4:
        return "dashdot"
    if len(d) >= 2:
        return "dotted" if d[0] <= d[1] else "dashed"
    return "dashed"


def _series_points(s, xcat):
    xs, ys = [], []
    for i, d in enumerate(s.get("data") or []):
        v = d.get("value") if isinstance(d, dict) else d
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            x, y = _num(v[0]), _num(v[1])
        else:
            x = _num(xcat[i]) if xcat and i < len(xcat) else float(i)
            y = _num(v)
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
    return np.array(xs), np.array(ys)


def _fmt_label(fmt, series_name, name, value):
    if not isinstance(fmt, str):
        return None
    v = value
    if isinstance(value, (list, tuple)):
        v = value[-1] if value else ""
    return (fmt.replace("{a}", str(series_name or "")).replace("{b}", str(name or ""))
               .replace("{c}", "" if v is None else (f"{v:g}" if isinstance(v, (int, float)) else str(v))))


def echarts_figure_facts(d):
    """Facts from one figure of an ECharts dump (echartkit/dump.mjs chartFacts + W/H/size_in/dpi/outputs)."""
    o = d["option"]
    xa = _as_list(o.get("xAxis"))
    ya = _as_list(o.get("yAxis"))
    xinfo = {a["index"]: a for a in d.get("xAxes", [])}
    yinfo = {a["index"]: a for a in d.get("yAxes", [])}
    grids = d.get("grids") or [None]
    gtxt = o.get("textStyle") or {}
    base_size = (gtxt.get("fontSize") or 12) / PT
    base_color = hexcolor(gtxt.get("color")) or "#333333"

    def axis_facts(opt, info, which):
        ext = info.get("extent") or [opt.get("min"), opt.get("max")]
        lo, hi = (_num(ext[0]), _num(ext[1])) if ext else (None, None)
        lab = opt.get("axisLabel") or {}
        custom = lab.get("customValues")
        ticks = [float(v) for v in (custom if custom else (info.get("ticks") or [])) if _num(v) is not None]
        log = opt.get("type") == "log"
        name_style = opt.get("nameTextStyle") or {}
        tick = opt.get("axisTick") or {}
        split = opt.get("splitLine") or {}
        minor = opt.get("minorTick") or {}
        show_labels = lab.get("show", True) is not False and opt.get("show", True) is not False
        return {"min": None if lo is None else min(lo, hi), "max": None if hi is None else max(lo, hi),
                "scale": "log" if log else "linear", "inverted": bool(opt.get("inverse")),
                "ticks": ticks, "step": tick_step(ticks, lo, hi, log) if lo is not None else None,
                "label": opt.get("name") or "",
                "label_size": (name_style.get("fontSize") / PT) if name_style.get("fontSize") else base_size,
                "label_color": hexcolor(name_style.get("color")) or base_color,
                "tick_size": ((lab.get("fontSize") / PT) if lab.get("fontSize") else base_size) if show_labels else None,
                "tick_color": (hexcolor(lab.get("color")) or base_color) if show_labels else None,
                "tick_direction": "in" if tick.get("inside") else "out",
                "minor": int(bool(minor.get("show")) and (info.get("minor") or 0)),
                "_split": bool(split.get("show")), "_grid": opt.get("gridIndex") or 0}

    palette = [hexcolor(c) for c in (o.get("color") or ECHARTS_PALETTE)]
    panels = []
    for gi in range(max(1, len(grids))):
        xs = [i for i, a in enumerate(xa) if (a.get("gridIndex") or 0) == gi]
        ys = [i for i, a in enumerate(ya) if (a.get("gridIndex") or 0) == gi]
        if not xs or not ys:
            continue
        xi = xs[0]
        left = [i for i in ys if ya[i].get("position") != "right"]
        right = [i for i in ys if ya[i].get("position") == "right"]
        y1i = (left or ys)[0]
        y2i = right[0] if right else (ys[1] if len(ys) > 1 and ys[1] != y1i else None)
        xfacts = axis_facts(xa[xi], xinfo.get(xi, {}), "x")
        y1f = axis_facts(ya[y1i], yinfo.get(y1i, {}), "y")
        y2f = axis_facts(ya[y2i], yinfo.get(y2i, {}), "y") if y2i is not None else None
        panel = {"x": xfacts, "y1": y1f, "y2": y2f, "lines": [], "spans": [], "vlines": [], "hlines": [],
                 "fills": 0, "grid": bool(xfacts.pop("_split") | y1f.pop("_split")), "title": "",
                 "_axes": {"x": xi, "y1": y1i, "y2": y2i}}
        xfacts.pop("_grid", None)
        y1f.pop("_grid", None)
        if y2f:
            y2f.pop("_split")
            y2f.pop("_grid", None)
        panels.append(panel)

    def panel_of(s):
        xi = s.get("xAxisIndex") or 0
        yi = s.get("yAxisIndex") or 0
        for p in panels:
            if p["_axes"]["x"] == xi and yi in (p["_axes"]["y1"], p["_axes"]["y2"]):
                return p, ("y2" if yi == p["_axes"]["y2"] and yi != p["_axes"]["y1"] else "y1")
        return (panels[0], "y1") if panels else (None, None)

    texts = []
    for si, s in enumerate(_as_list(o.get("series"))):
        if s.get("type") not in ("line", "scatter", "bar", None):
            continue
        p, axis = panel_of(s)
        if p is None:
            continue
        xcat = xa[p["_axes"]["x"]].get("data") if xa else None
        xs, ys = _series_points(s, xcat)
        ls = s.get("lineStyle") or {}
        its = s.get("itemStyle") or {}
        color = hexcolor(ls.get("color")) or hexcolor(s.get("color")) or hexcolor(its.get("color")) \
            or palette[si % len(palette)]
        if xs.size >= 5:
            kind = "scatter" if s.get("type") == "scatter" else "line"
            t = ls.get("type", "solid")
            style = _dash_array(t) if isinstance(t, list) else _style(t)
            if kind == "line" and (ls.get("width") == 0 or ls.get("opacity") == 0):
                kind, style = "scatter", "none"
            marker = kind == "scatter" or (s.get("showSymbol", True) is not False and s.get("symbol") not in ("none", None))
            p["lines"].append({"axis": axis, "kind": kind, "color": color,
                               "width": float(ls.get("width", 2)) / PT if kind == "line" else 0.0,
                               "style": style if kind == "line" else "none", "marker": bool(marker),
                               "n": int(xs.size), "x_range": _rng(xs), "y_range": _rng(ys),
                               "label": s.get("name") or ""})
            if s.get("areaStyle"):
                p["fills"] += 1
        # markLine / markArea / markPoint: lines, spans and their texts
        ml = s.get("markLine") or {}
        for item in ml.get("data") or []:
            pair = item if isinstance(item, list) else None
            one = pair[0] if pair else item
            if not isinstance(one, dict):
                continue
            lbl = (one.get("label") or {}) if isinstance(one.get("label"), dict) else {}
            mlab = ml.get("label") or {}
            text = one.get("name") if (lbl.get("show", mlab.get("show", True)) is not False) else None
            fmt = lbl.get("formatter", mlab.get("formatter"))
            if pair and isinstance(pair[1], dict) and "coord" in one and "coord" in pair[1]:
                c0, c1 = one["coord"], pair[1]["coord"]
                txt = _fmt_label(fmt, s.get("name"), one.get("name"), None) if fmt else text
                if txt:
                    texts.append({"text": txt, "x": _num(c1[0]), "y": _num(c1[1]), "axis": axis,
                                  "color": hexcolor(lbl.get("color") or mlab.get("color")), "size": None,
                                  "panel": panels.index(p)})
                continue
            v = one.get("xAxis")
            if v is not None and _num(v) is not None and not pair:
                p["vlines"].append({"x": _num(v), "color": hexcolor((one.get("lineStyle") or ml.get("lineStyle") or {}).get("color")),
                                    "style": "dashed"})
                txt = _fmt_label(fmt, s.get("name"), one.get("name"), v) if fmt else text
                if txt and (lbl.get("show", mlab.get("show", True)) is not False):
                    texts.append({"text": txt, "x": _num(v), "y": None, "axis": axis, "color": None, "size": None,
                                  "panel": panels.index(p)})
            v = one.get("yAxis")
            if v is not None and _num(v) is not None and not pair:
                p["hlines"].append({"y": _num(v), "axis": axis, "color": None, "style": "dashed"})
                txt = _fmt_label(fmt, s.get("name"), one.get("name"), v) if fmt else text
                if txt and (lbl.get("show", mlab.get("show", True)) is not False):
                    texts.append({"text": txt, "x": None, "y": _num(v), "axis": axis, "color": None, "size": None,
                                  "panel": panels.index(p)})
        ma = s.get("markArea") or {}
        for item in ma.get("data") or []:
            if isinstance(item, list) and len(item) == 2 and all(isinstance(e, dict) for e in item):
                a, b = item
                if a.get("xAxis") is not None and b.get("xAxis") is not None and a.get("yAxis") is None:
                    x0, x1 = _num(a.get("xAxis")), _num(b.get("xAxis"))
                    if x0 is not None and x1 is not None:
                        col = (a.get("itemStyle") or ma.get("itemStyle") or {}).get("color")
                        p["spans"].append({"x_min": min(x0, x1), "x_max": max(x0, x1), "color": hexcolor(col)})
                        nm = a.get("name") or (a.get("label") or {}).get("formatter")
                        if nm:
                            texts.append({"text": str(nm), "x": (x0 + x1) / 2, "y": None, "axis": "y1", "color": None,
                                          "size": None, "panel": panels.index(p)})
        mp = s.get("markPoint") or {}
        for item in mp.get("data") or []:
            if not isinstance(item, dict):
                continue
            x = y = None
            if "coord" in item:
                x, y = _num(item["coord"][0]), _num(item["coord"][1])
            elif item.get("type") in ("max", "min") and xs.size:
                k = int(np.argmax(ys) if item["type"] == "max" else np.argmin(ys))
                x, y = float(xs[k]), float(ys[k])
            elif "xAxis" in item and "yAxis" in item:
                x, y = _num(item["xAxis"]), _num(item["yAxis"])
            lbl = item.get("label") or {}
            mlab = mp.get("label") or {}
            if lbl.get("show", mlab.get("show", True)) is False:
                continue
            fmt = lbl.get("formatter", mlab.get("formatter"))
            value = item.get("value", y)
            txt = _fmt_label(fmt, s.get("name"), item.get("name"), value) if fmt else (
                f"{value:g}" if isinstance(value, (int, float)) else (str(value) if value is not None else None))
            if txt:
                texts.append({"text": txt, "x": x, "y": y, "axis": axis, "color": hexcolor(lbl.get("color")),
                              "size": (lbl.get("fontSize") / PT) if lbl.get("fontSize") else None,
                              "panel": panels.index(p)})
        lab = s.get("label") or {}
        if lab.get("show") and xs.size and xs.size < 30:
            for x, y in zip(xs, ys):
                texts.append({"text": f"{y:g}", "x": float(x), "y": float(y), "axis": axis, "color": None,
                              "size": None, "panel": panels.index(p)})

    for t in d.get("texts") or []:
        g = t.get("grid", -1)
        pi = g if 0 <= g < len(panels) else 0
        data = t.get("data") or [None]
        xy = data[0] if data and data[0] else [None, None]
        texts.append({"text": t["text"], "x": _num(xy[0]), "y": _num(xy[1]), "axis": "y1",
                      "color": hexcolor(t.get("fill")) or base_color,
                      "size": (t["fontSize"] / PT) if t.get("fontSize") else None, "panel": pi if panels else None})

    title = None
    for t in _as_list(o.get("title")):
        if t.get("show", True) is not False and (t.get("text") or "").strip():
            ts = t.get("textStyle") or {}
            title = {"text": t["text"], "size": (ts.get("fontSize") / PT) if ts.get("fontSize") else 18 / PT,
                     "color": hexcolor(ts.get("color")) or base_color}
            break

    legend = {"shown": False, "entries": [], "size": None, "inside": None, "where": None}
    lgs = _as_list(o.get("legend"))
    boxes = d.get("legends") or []
    for li, lg in enumerate(lgs):
        if lg.get("show", True) is False:
            continue
        names = [n if isinstance(n, str) else (n or {}).get("name") for n in (lg.get("data") or [])]
        if not names:
            names = [s.get("name") for s in _as_list(o.get("series"))
                     if s.get("name") and not str(s.get("name")).startswith("__") and s.get("data")]
        names = [n for n in names if n]
        if not names:
            continue
        box = boxes[li] if li < len(boxes) else None
        g0 = grids[0] if grids and grids[0] else None
        inside = where = None
        if box and g0 and box.get("width"):
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            inside = g0["x"] - 2 <= cx <= g0["x"] + g0["width"] + 2 and g0["y"] - 2 <= cy <= g0["y"] + g0["height"] + 2
            # pixel y grows downwards: flip so "upper" means near the top
            where = _where(cx, -cy, (g0["x"], -(g0["y"] + g0["height"]), g0["x"] + g0["width"], -g0["y"])) if inside else "outside"
        ts = lg.get("textStyle") or {}
        legend = {"shown": True, "entries": names, "size": (ts.get("fontSize") / PT) if ts.get("fontSize") else base_size,
                  "inside": inside, "where": where, "colors": [hexcolor(ts.get("color")) or base_color]}
        break

    for p in panels:
        p.pop("_axes", None)
    W, H = d.get("W") or 640, d.get("H") or 480
    files = [file_entry(o_["path"], o_["format"]) for o_ in d.get("outputs") or []]
    return {"engine": "echarts", "size_in": d.get("size_in") or [W / 96, H / 96], "dpi": d.get("dpi"),
            "title": title, "panels": panels, "texts": texts, "legend": legend, "files": files}


def echarts_dump_facts(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return [echarts_figure_facts(f) for f in d.get("figures", [])]


# =================================================================== plotkit specs
def plotkit_facts(spec, engine, dump_path):
    """Draw a spec with plotkit on one engine and return (result, facts). Raises PlotkitError like plotkit."""
    import sys
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import plotkit
    if engine == "matplotlib":
        install_mpl_hook()
        take_mpl_facts()
        try:
            res = plotkit.plot(spec, engine="matplotlib")
        finally:
            figs = take_mpl_facts()
        for f in figs:
            for e in f["files"]:
                e.update(file_entry(e["path"], e["format"]))
        return res, figs
    old = os.environ.get("PLOTKIT_DUMP_OPTION")
    os.environ["PLOTKIT_DUMP_OPTION"] = str(dump_path)
    try:
        Path(dump_path).unlink(missing_ok=True)
        res = plotkit.plot(spec, engine="echarts")
    finally:
        if old is None:
            os.environ.pop("PLOTKIT_DUMP_OPTION", None)
        else:
            os.environ["PLOTKIT_DUMP_OPTION"] = old
    return res, echarts_dump_facts(dump_path)
