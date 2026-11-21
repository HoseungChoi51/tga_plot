"""Chart facts: what a bar / line / scatter / histogram / heatmap / pie figure actually shows, in one JSON
shape for matplotlib figures (chartkit or model-written code) and ECharts options (chartkit or model-written).

    facts  = {"engine", "size_in", "dpi", "title", "panels": [panel], "texts": [str], "legend": {...}, "files": [...]}
    panel  = {"x": axis, "y": axis, "bars": [bar series], "lines": [line], "points": [points], "hist": [hist],
              "heatmap": heat | None, "pie": pie | None, "hlines": [y], "vlines": [x], "value_labels": int, "texts": [str]}
    axis   = {"label", "type" (category|value|time), "categories", "min", "max", "log", "inverted"}
    bar series = {"name", "orient" (v|h), "cats": [label], "values": [float], "bottoms": [float], "colors": [hex]}
    line   = {"name", "n", "x": [..], "y": [..], "color", "style"};  points = {"name", "n", "x_range", "y_range", "color"}
    hist   = {"name", "edges": [..], "counts": [..], "color"}
    heat   = {"rows": [label], "cols": [label], "z": [[float]], "colorbar": bool, "values_shown": bool}
    pie    = {"labels": [label], "shares": [float], "values": [float] | None, "colors": [hex]}
"""
import json
import math
import re
from pathlib import Path

import numpy as np

from facts import file_entry, hexcolor, _where


def _f(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# =================================================================== matplotlib
def _tick_map(ax, which):
    """[(position, label)] of the labelled major ticks."""
    a = ax.xaxis if which == "x" else ax.yaxis
    out = []
    try:
        locs = a.get_majorticklocs()
        labs = [t.get_text() for t in a.get_majorticklabels()]
        for p, l in zip(locs, labs):
            if l.strip():
                out.append((float(p), l.strip()))
    except Exception:  # noqa: BLE001
        pass
    return out


def _cat_at(ticks, pos, width):
    if not ticks:
        return None
    p, lab = min(ticks, key=lambda t: abs(t[0] - pos))
    return lab if abs(p - pos) <= max(width, 0.5) else None


def _axis(ax, which, categorical):
    lo, hi = ax.get_xlim() if which == "x" else ax.get_ylim()
    a = ax.xaxis if which == "x" else ax.yaxis
    scale = ax.get_xscale() if which == "x" else ax.get_yscale()
    conv = getattr(a, "converter", None) or getattr(a, "get_converter", lambda: None)()
    is_time = conv is not None and "date" in type(conv).__name__.lower()
    labs = [l for _, l in _tick_map(ax, which)]
    ticks = [float(v) for v in a.get_majorticklocs() if min(lo, hi) - 1e-9 <= v <= max(lo, hi) + 1e-9]
    return {"label": a.label.get_text(), "type": "category" if categorical else ("time" if is_time else "value"),
            "ticks": ticks, "step": _step(ticks),
            "categories": labs if categorical else None, "min": float(min(lo, hi)), "max": float(max(lo, hi)),
            "log": scale == "log", "inverted": bool(lo > hi), "tick_labels": labs,
            "rotate": float(a.get_majorticklabels()[0].get_rotation()) if a.get_majorticklabels() else 0.0}


def mpl_chart_facts(fig):
    from matplotlib.collections import PathCollection, QuadMesh, PolyCollection
    from matplotlib.container import BarContainer
    from matplotlib.image import AxesImage
    from matplotlib.patches import Rectangle, Wedge
    renderer = fig.canvas.get_renderer()
    axes = [a for a in fig.axes if a.get_visible()]
    cbar_axes = set()
    for a in axes:                         # colour bars are axes too
        for im in list(a.images) + [c for c in a.collections if isinstance(c, QuadMesh)]:
            cb = getattr(im, "colorbar", None)
            if cb is not None:
                cbar_axes.add(cb.ax)
    panels, all_texts = [], []
    for ax in axes:
        if ax in cbar_axes:
            continue
        p = {"bars": [], "lines": [], "points": [], "hist": [], "heatmap": None, "pie": None, "hlines": [], "vlines": [],
             "value_labels": 0, "texts": []}
        xt, yt = _tick_map(ax, "x"), _tick_map(ax, "y")
        # bars and histograms
        for c in ax.containers:
            if not isinstance(c, BarContainer):
                continue
            rects = [r for r in c.patches if r.get_visible()]
            if not rects:
                continue
            horiz = getattr(c, "orientation", "vertical") == "horizontal"
            xs = np.array([r.get_x() for r in rects]); ws = np.array([r.get_width() for r in rects])
            ys = np.array([r.get_y() for r in rects]); hs = np.array([r.get_height() for r in rects])
            name = c.get_label() if c.get_label() and not c.get_label().startswith("_") else ""
            if not horiz:
                centers, size, base, val = xs + ws / 2, ws, ys, hs
                ticks = xt
            else:
                centers, size, base, val = ys + hs / 2, hs, xs, ws
                ticks = yt
            cats = [_cat_at(ticks, cc, s / 2) for cc, s in zip(centers, size)]
            colors = [hexcolor(r.get_facecolor()) for r in rects]
            numeric_ticks = all(re.fullmatch(r"[-−+]?[\d.,]+(e[-+]?\d+)?", l) for _, l in ticks) if ticks else True
            if not horiz and len(rects) >= 3 and np.allclose(xs[1:], (xs + ws)[:-1], atol=1e-9 * max(1.0, float(np.abs(xs).max()))) \
                    and (numeric_ticks or sum(c_ is not None for c_ in cats) < len(cats) / 2):
                p["hist"].append({"name": name, "edges": [float(v) for v in xs] + [float(xs[-1] + ws[-1])],
                                  "counts": [float(v) for v in hs], "bottoms": [float(v) for v in ys], "color": colors[0]})
            else:
                p["bars"].append({"name": name, "orient": "h" if horiz else "v",
                                  "cats": [c_ if c_ is not None else _num_label(cc) for c_, cc in zip(cats, centers)],
                                  "values": [float(v) for v in val], "bottoms": [float(v) for v in base], "colors": colors,
                                  "centers": [float(v) for v in centers]})
        # lines and points
        from matplotlib.container import ErrorbarContainer
        err_lines = set()
        for c in ax.containers:
            if isinstance(c, ErrorbarContainer):
                for part in c.lines:
                    for q in (part if isinstance(part, (tuple, list)) else [part]):
                        if q is not None:
                            err_lines.add(id(q))
        for ln in ax.get_lines():
            if not ln.get_visible() or id(ln) in err_lines:
                continue
            xd = np.asarray(ln.get_xdata(orig=False), dtype=object)
            yd = np.asarray(ln.get_ydata(orig=False), dtype=float)
            try:
                xf = np.asarray(ln.get_xdata(orig=False), dtype=float)
            except (TypeError, ValueError):
                import matplotlib.dates as mdates
                xf = np.asarray(mdates.date2num(list(xd)), dtype=float)
            name = "" if ln.get_label().startswith("_") else ln.get_label()
            if xf.size == 2 and xf[0] == xf[1] and yd[0] != yd[1]:
                p["vlines"].append(float(xf[0]))
                continue
            if yd.size == 2 and yd[0] == yd[1] and xf[0] != xf[1]:
                p["hlines"].append(float(yd[0]))
                continue
            if xf.size < 2:
                continue
            ls = ln.get_linestyle()
            marker = ln.get_marker() not in (None, "None", "", " ", "none")
            if ls in ("None", "none", "", " ") and marker:
                ok = np.isfinite(xf) & np.isfinite(yd)
                p["points"].append({"name": name, "n": int(ok.sum()), "x_range": _rng(xf[ok]), "y_range": _rng(yd[ok]),
                                    "color": hexcolor(ln.get_color()), "x": xf[ok].tolist(), "y": yd[ok].tolist()})
            else:
                p["lines"].append({"name": name, "n": int(xf.size), "x": [_f(v) for v in xf], "y": [_f(v) for v in yd],
                                   "color": hexcolor(ln.get_color()), "style": ls, "width": float(ln.get_linewidth())})
        for coll in ax.collections:
            if not coll.get_visible():
                continue
            if isinstance(coll, PathCollection):
                off = np.asarray(coll.get_offsets(), dtype=float)
                if len(off):
                    fc = coll.get_facecolor()
                    p["points"].append({"name": "" if str(coll.get_label()).startswith("_") else str(coll.get_label()),
                                        "n": int(len(off)), "x_range": _rng(off[:, 0]), "y_range": _rng(off[:, 1]),
                                        "color": hexcolor(fc[0]) if len(fc) else None,
                                        "colors": sorted({hexcolor(c) for c in fc}) if len(fc) > 1 else None,
                                        "x": off[:, 0].tolist(), "y": off[:, 1].tolist()})
            elif isinstance(coll, QuadMesh):
                arr = np.asarray(coll.get_array(), dtype=float)
                try:
                    shp = coll._coordinates.shape
                    arr = arr.reshape(shp[0] - 1, shp[1] - 1)
                except Exception:  # noqa: BLE001
                    pass
                p["heatmap"] = _heat(ax, arr, xt, yt, getattr(coll, "colorbar", None) is not None)
                p["heatmap"].update(cmap=coll.get_cmap().name, clim=[_f(v) for v in coll.get_clim()])
        for im in ax.images:
            arr = np.ma.filled(np.ma.asarray(im.get_array(), dtype=float), np.nan)
            if arr.ndim == 2:
                p["heatmap"] = _heat(ax, arr, xt, yt, getattr(im, "colorbar", None) is not None, image=True)
                p["heatmap"].update(cmap=im.get_cmap().name, clim=[_f(v) for v in im.get_clim()])
        # pie
        wedges = [w for w in ax.patches if isinstance(w, Wedge) and w.get_visible()]
        if wedges:
            spans = [((w.theta2 - w.theta1) % 360) or 360 for w in wedges]
            tot = sum(spans)
            labels = []
            for w in wedges:
                mid = math.radians((w.theta1 + w.theta2) / 2)
                cx, cy = w.center
                best, bd = None, 1e9
                for t in ax.texts:
                    s = t.get_text().strip()
                    if not s or re.fullmatch(r"[\d.,\s%()]+", s):
                        continue
                    tx, ty = t.get_position()
                    ang = math.atan2(ty - cy, tx - cx)
                    d = abs(math.atan2(math.sin(ang - mid), math.cos(ang - mid)))
                    if d < bd:
                        best, bd = s, d
                labels.append(best if bd < math.radians(max(15, (w.theta2 - w.theta1) / 2 + 5)) else (w.get_label() if not str(w.get_label()).startswith("_") else None))
            leg = ax.get_legend()
            if leg is not None and all(l is None for l in labels):
                labels = [t.get_text() for t in leg.get_texts()][:len(wedges)]
            p["pie"] = {"labels": labels, "shares": [s / tot for s in spans], "values": None,
                        "colors": [hexcolor(w.get_facecolor()) for w in wedges]}
        # texts
        for t in ax.texts:
            s = t.get_text().strip()
            if s and t.get_visible():
                p["texts"].append(s)
        p["value_labels"] = _count_value_labels(ax, p)
        has_cat_x = bool(p["bars"]) and p["bars"][0]["orient"] == "v" or (p["heatmap"] is not None)
        has_cat_y = bool(p["bars"]) and p["bars"][0]["orient"] == "h" or (p["heatmap"] is not None)
        if p["lines"] and not p["bars"] and xt and all(not re.fullmatch(r"[-−+\d.,e]+", l) for _, l in xt):
            has_cat_x = True
        p["x"] = _axis(ax, "x", has_cat_x)
        p["y"] = _axis(ax, "y", has_cat_y)
        p["title"] = ax.get_title() or ax.get_title("left") or ax.get_title("right")
        if p["bars"] or p["lines"] or p["points"] or p["hist"] or p["heatmap"] or p["pie"]:
            panels.append(p)
        all_texts += p["texts"]
    for t in fig.texts:
        if t.get_text().strip():
            all_texts.append(t.get_text().strip())
    title = None
    sup = getattr(fig, "_suptitle", None)
    if sup is not None and sup.get_text().strip():
        title = sup.get_text().strip()
    for p in panels:
        if not title and p.get("title"):
            title = p["title"]
    legend = {"shown": False, "entries": [], "inside": None, "where": None}
    for lg in [a.get_legend() for a in axes if a.get_legend() is not None] + list(fig.legends):
        if not lg.get_visible():
            continue
        entries = [t.get_text() for t in lg.get_texts() if t.get_text()]
        if not entries:
            continue
        bb = lg.get_window_extent(renderer)
        host = next((a for a in axes if a not in cbar_axes), axes[0]).get_window_extent(renderer)
        cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
        inside = host.x0 - 2 <= cx <= host.x1 + 2 and host.y0 - 2 <= cy <= host.y1 + 2
        legend = {"shown": True, "entries": legend["entries"] + entries, "inside": bool(inside),
                  "where": _where(cx, cy, (host.x0, host.y0, host.x1, host.y1)) if inside else "outside"}
    return {"engine": "matplotlib", "size_in": [float(v) for v in fig.get_size_inches()], "dpi": None, "title": title,
            "panels": panels, "texts": all_texts, "legend": legend, "files": []}


def _step(ticks):
    t = sorted(ticks)
    if len(t) < 3:
        return None
    d = np.diff(t)
    inner = d[1:-1] if len(d) > 2 else d
    st = float(np.median(inner))
    return round(st, 10) if st > 0 else None


def _r(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or np.std(x[ok]) == 0 or np.std(y[ok]) == 0:
        return None
    return float(np.corrcoef(x[ok], y[ok])[0, 1])


def _num_label(v):
    v = float(v)
    return str(int(v)) if v.is_integer() else f"{v:g}"


def _rng(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    return [float(a.min()), float(a.max())] if a.size else None


def _heat(ax, arr, xt, yt, colorbar, image=False):
    nr, nc = arr.shape
    def labels(ticks, n):
        out = [None] * n
        for pos, lab in ticks:
            k = int(round(pos - (0 if image else 0.5)))
            if 0 <= k < n:
                out[k] = lab
        return out
    rows, cols = labels(yt, nr), labels(xt, nc)
    lo, hi = ax.get_ylim()
    texts = 0
    for t in ax.texts:
        if re.fullmatch(r"\s*[-−+]?[\d.,]+(e[-+]?\d+)?\s*%?\s*", t.get_text() or ""):
            texts += 1
    z = arr.tolist()
    if not image and not (lo > hi):
        z, rows = z[::-1], rows[::-1]
    return {"rows": rows, "cols": cols, "z": [[_f(v) for v in r] for r in z], "colorbar": bool(colorbar),
            "values_shown": texts >= 0.5 * nr * nc}


def _count_value_labels(ax, p):
    n = 0
    for t in ax.texts:
        if re.fullmatch(r"\s*[-−+]?[\d.,]+(e[-+]?\d+)?\s*%?\s*", t.get_text() or ""):
            n += 1
    return n


# =================================================================== ECharts
def _val(d):
    if isinstance(d, dict):
        d = d.get("value")
    return d


def _axis_e(opt_axis, info):
    a = opt_axis[0] if isinstance(opt_axis, list) else (opt_axis or {})
    t = a.get("type", "value")
    ext = (info or {}).get("extent") or [a.get("min"), a.get("max")]
    custom = (a.get("axisLabel") or {}).get("customValues")          # plotkit sets the tick values itself
    ticks = [float(v) for v in (custom or (info or {}).get("ticks") or []) if isinstance(v, (int, float))] if t != "category" else []
    return {"label": a.get("name") or "", "type": "category" if t == "category" else ("time" if t == "time" else "value"),
            "ticks": ticks, "step": _step(ticks),
            "categories": [str(_val(c)) for c in (a.get("data") or [])] if t == "category" else None,
            "min": _f(ext[0]) if ext else None, "max": _f(ext[1]) if ext else None, "log": t == "log",
            "inverted": bool(a.get("inverse")), "tick_labels": None,
            "rotate": _f((a.get("axisLabel") or {}).get("rotate")) or 0.0}


def echarts_chart_facts(d):
    """d: one figure from a PLOTKIT_DUMP_OPTION dump (chartFacts + W, H, dpi, outputs)."""
    opt = d["option"]
    xa = opt.get("xAxis") or [{}]
    ya = opt.get("yAxis") or [{}]
    xa = xa if isinstance(xa, list) else [xa]
    ya = ya if isinstance(ya, list) else [ya]
    xinfo = (d.get("xAxes") or [None])[0]
    yinfo = (d.get("yAxes") or [None])[0]
    p = {"bars": [], "lines": [], "points": [], "hist": [], "heatmap": None, "pie": None, "hlines": [], "vlines": [],
         "value_labels": 0, "texts": [t["text"] for t in d.get("texts", [])]}
    xcats = [str(_val(c)) for c in (xa[0].get("data") or [])] if xa[0].get("type") == "category" else None
    ycats = [str(_val(c)) for c in (ya[0].get("data") or [])] if ya[0].get("type") == "category" else None
    stacks = {}
    for s in opt.get("series") or []:
        t = s.get("type")
        name = s.get("name") or ""
        data = s.get("data") or []
        lab = s.get("label") or {}
        color = hexcolor(((s.get("itemStyle") or {}).get("color")) or ((s.get("lineStyle") or {}).get("color")))
        for ml in ((s.get("markLine") or {}).get("data") or []):
            if isinstance(ml, dict):
                if ml.get("yAxis") is not None:
                    (p["hlines"] if not ycats else p["vlines"]).append(_f(ml["yAxis"]) if _f(ml["yAxis"]) is not None else ml["yAxis"])
                if ml.get("xAxis") is not None:
                    p["vlines"].append(_f(ml["xAxis"]) if _f(ml["xAxis"]) is not None else ml["xAxis"])
        for v in data:                       # labels written as plain text per item (chartkit does this)
            if isinstance(v, dict) and isinstance((v.get("label") or {}).get("formatter"), str):
                p["texts"].append(v["label"]["formatter"])
        if isinstance(lab.get("formatter"), str) and lab.get("show") and "{" not in lab["formatter"]:
            p["texts"].append(lab["formatter"])
        if t == "bar":
            horiz = ycats is not None and xcats is None
            cats = ycats if horiz else xcats
            vals, cols = [], []
            for k, v in enumerate(data):
                vv = _val(v)
                if isinstance(vv, list):           # [x, y] pairs
                    vv = vv[0 if horiz else 1]
                vals.append(_f(vv))
                cols.append(hexcolor(((v.get("itemStyle") or {}).get("color")) if isinstance(v, dict) and v.get("itemStyle") else None) or color)
            key = s.get("stack")
            bottoms = [0.0] * len(vals)
            if key:
                prev = stacks.get(key, [0.0] * len(vals))
                bottoms = prev[:len(vals)] + [0.0] * (len(vals) - len(prev))
                stacks[key] = [b + (v or 0) for b, v in zip(bottoms, vals)]
            p["bars"].append({"name": name, "orient": "h" if horiz else "v",
                              "cats": (cats or [str(k) for k in range(len(vals))])[:len(vals)], "values": vals,
                              "bottoms": bottoms, "colors": cols})
            if lab.get("show"):
                p["value_labels"] += sum(v is not None for v in vals)
        elif t == "line":
            xs, ys = [], []
            for k, v in enumerate(data):
                vv = _val(v)
                if isinstance(vv, list):
                    xs.append(vv[0])
                    ys.append(_f(vv[1]))
                else:
                    xs.append(xcats[k] if xcats and k < len(xcats) else k)
                    ys.append(_f(vv))
            if len(xs) >= 2:
                p["lines"].append({"name": name, "n": len(xs), "x": xs, "y": ys, "color": color,
                                   "style": ((s.get("lineStyle") or {}).get("type") or "solid")})
        elif t in ("scatter", "effectScatter"):
            pts = [_val(v) for v in data]
            pts = [q for q in pts if isinstance(q, list) and len(q) >= 2]
            xs = [_f(q[0]) if _f(q[0]) is not None else q[0] for q in pts]
            ys = [_f(q[1]) for q in pts]
            xn = [v for v in xs if isinstance(v, float)]
            item_cols = sorted({hexcolor((v.get("itemStyle") or {}).get("color")) for v in data
                                if isinstance(v, dict) and v.get("itemStyle")} - {None})
            p["points"].append({"name": name, "n": len(pts), "x_range": _rng(xn) if xn else None, "y_range": _rng([v for v in ys if v is not None]),
                                "color": color, "colors": item_cols or None,
                                "x": xs if xn and len(xn) == len(xs) else None, "y": ys})
        elif t == "custom" and data and isinstance(_val(data[0]), list) and len(_val(data[0])) >= 3 \
                and (s.get("encode") or {}).get("x") == [0, 1]:
            rows = [_val(v) for v in data]
            p["hist"].append({"name": name, "edges": [float(r[0]) for r in rows] + [float(rows[-1][1])],
                              "counts": [float(r[2]) for r in rows], "bottoms": [float(r[3]) if len(r) > 3 else 0.0 for r in rows],
                              "color": color})
        elif t == "heatmap":
            rows = ycats or []
            cols = xcats or []
            z = [[None] * len(cols) for _ in rows]
            for v in data:
                vv = _val(v)
                if isinstance(vv, list) and len(vv) >= 3:
                    i = rows.index(str(vv[1])) if not isinstance(vv[1], (int, float)) else int(vv[1])
                    j = cols.index(str(vv[0])) if not isinstance(vv[0], (int, float)) else int(vv[0])
                    if 0 <= i < len(rows) and 0 <= j < len(cols):
                        z[i][j] = _f(vv[2])
            yinv = bool((ya[0] or {}).get("inverse"))
            if not yinv:                          # ECharts draws row 0 at the bottom unless inverse
                z, rows = z[::-1], rows[::-1]
            vm = opt.get("visualMap")
            vm = vm[0] if isinstance(vm, list) and vm else (vm or {})
            shown = bool(lab.get("show")) or any(isinstance(v, dict) and (v.get("label") or {}).get("show") for v in data)
            p["heatmap"] = {"rows": rows, "cols": cols, "z": z, "colorbar": bool(vm), "values_shown": shown,
                            "cmap": None, "ramp": [hexcolor(c) for c in ((vm.get("inRange") or {}).get("color") or [])],
                            "clim": [_f(vm.get("min")), _f(vm.get("max"))] if vm else None}
        elif t == "pie":
            items = [v for v in data if isinstance(v, dict)]
            vals = [_f(v.get("value")) or 0.0 for v in items]
            tot = sum(vals) or 1.0
            p["pie"] = {"labels": [str(v.get("name")) for v in items], "shares": [v / tot for v in vals], "values": vals,
                        "colors": [hexcolor((v.get("itemStyle") or {}).get("color")) for v in items]}
    p["x"] = _axis_e(xa, xinfo)
    p["y"] = _axis_e(ya, yinfo)
    title = opt.get("title")
    title = title[0] if isinstance(title, list) and title else title
    ttext = (title or {}).get("text") if (title or {}).get("show", True) is not False else None
    leg = opt.get("legend")
    leg = leg[0] if isinstance(leg, list) and leg else leg
    legend = {"shown": False, "entries": [], "inside": None, "where": None}
    if leg and leg.get("show", True) is not False:
        entries = [str(_val(x)) if not isinstance(x, dict) else str(x.get("name")) for x in (leg.get("data") or [])] or \
                  [s.get("name") for s in (opt.get("series") or []) if s.get("name")]
        box = (d.get("legends") or [None])[0]
        grid = (d.get("grids") or [None])[0]
        inside, where = None, None
        if box and grid:
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            inside = grid["x"] - 2 <= cx <= grid["x"] + grid["width"] + 2 and grid["y"] - 2 <= cy <= grid["y"] + grid["height"] + 2
            H = d.get("H", 0)
            where = _where(cx, H - cy, (grid["x"], H - grid["y"] - grid["height"], grid["x"] + grid["width"], H - grid["y"])) if inside else "outside"
        legend = {"shown": bool(entries), "entries": entries, "inside": inside, "where": where}
    return {"engine": "echarts", "size_in": d.get("size_in"), "dpi": d.get("dpi"), "title": ttext,
            "panels": [p], "texts": p["texts"] + ([ttext] if ttext else []), "legend": legend,
            "files": [file_entry(o["path"], o["format"]) for o in d.get("outputs", [])]}


def echarts_dump_chart_facts(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return [echarts_chart_facts(f) for f in d.get("figures", [])]


_HOOK = {"installed": False, "figs": [], "out": None}


def install_hook(out_path=None):
    """Record chart facts of every Figure saved from now on (once per figure), also written to out_path."""
    from matplotlib.figure import Figure
    _HOOK["out"] = out_path
    if _HOOK["installed"]:
        return _HOOK
    orig = Figure.savefig

    def savefig(self, fname, *args, **kw):
        res = orig(self, fname, *args, **kw)
        try:
            rec = next((r for r in _HOOK["figs"] if r["id"] == id(self)), None)
            if rec is None:
                rec = {"id": id(self), "facts": mpl_chart_facts(self)}
                _HOOK["figs"].append(rec)
            if isinstance(fname, (str, Path)):
                rec["facts"]["files"].append(file_entry(str(fname), kw.get("format")))
        except Exception as e:  # noqa: BLE001 - never break the plot because of the recorder
            _HOOK.setdefault("errors", []).append(f"{type(e).__name__}: {e}")
        if _HOOK["out"]:
            Path(_HOOK["out"]).write_text(json.dumps({"figures": [r["facts"] for r in _HOOK["figs"]],
                                                      "errors": _HOOK.get("errors", [])}, ensure_ascii=False))
        return res

    Figure.savefig = savefig
    _HOOK["installed"] = True
    return _HOOK


def take():
    """The facts recorded since the last take()."""
    out = [r["facts"] for r in _HOOK["figs"]]
    _HOOK["figs"] = []
    return out
