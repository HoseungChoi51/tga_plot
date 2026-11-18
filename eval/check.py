"""Check figure facts (eval/facts.py) against the expected facts of one request.

A check is a dict with one type key plus options, and a category:
  "data" - the right data is drawn, "ask" - what the user asked for, "conv" - the lab's conventions
  that a TGA plot here always has (residue label, DTG peak label), asked or not.

    ok, results = run_checks(figures, checks)     results: [{"check", "cat", "ok", "why"}]
"""
import re

import numpy as np
from matplotlib.colors import to_rgb

NUM = re.compile(r"[-+−]?\d+(?:\.\d+)?")


# =================================================================== helpers
def nums(text):
    return [float(m.replace("−", "-")) for m in NUM.findall(text or "")]


def rgb(c):
    try:
        return np.array(to_rgb(c))
    except (ValueError, TypeError):
        return None


def color_ok(actual, target):
    a, t = rgb(actual), rgb(target)
    if a is None or t is None:
        return False
    tname = str(target).lower()
    if tname in ("gray", "grey", "dimgray", "dimgrey", "darkgray", "darkgrey", "회색"):
        return float(np.ptp(a)) < 0.08 and 0.25 <= float(a.mean()) <= 0.8
    if tname == "black":
        return float(a.max()) < 0.2
    if tname == "white":
        return float(a.min()) > 0.85
    return float(np.linalg.norm(a - t)) < 0.3


def close(a, b, tol):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


PX_PER_PT = 96 / 72


def size_ok(got, want, fig, tol=0.6):
    """Font sizes are in points; an ECharts option counts sizes in px, so "크기 18" written as fontSize 18
    (px) is also accepted on ECharts figures."""
    return close(got, want, tol) or (fig.get("engine") == "echarts" and got is not None
                                      and close(float(got) * PX_PER_PT, want, tol))


def range_ok(rng, want, tol, allow_neg=False):
    if not rng or not want:
        return False
    span = abs(want[1] - want[0]) or 1.0
    t = tol * span
    if abs(rng[0] - want[0]) <= t and abs(rng[1] - want[1]) <= t:
        return True
    return allow_neg and abs(rng[0] + want[1]) <= t and abs(rng[1] + want[0]) <= t


def data_figs(figs):
    return [f for f in figs if any(p["lines"] for p in f["panels"])] or figs


def all_lines(figs, axis="any"):
    for fi, f in enumerate(figs):
        for pi, p in enumerate(f["panels"]):
            for ln in p["lines"]:
                if axis in ("any", ln["axis"]):
                    yield fi, pi, ln


def plot_texts(figs):
    for f in figs:
        for t in f["texts"]:
            yield t


def every_text(figs):
    """All visible strings: plot texts, title, axis labels, legend entries."""
    for f in figs:
        for t in f["texts"]:
            yield t["text"]
        if f.get("title"):
            yield f["title"]["text"]
        for p in f["panels"]:
            for ax in ("x", "y1", "y2"):
                if p.get(ax):
                    yield p[ax]["label"]
            if p.get("title"):
                yield p["title"]
        yield from f["legend"].get("entries") or []


def norm(s):
    return re.sub(r"\s+", "", str(s or "")).replace("−", "-").lower()


# =================================================================== checks
def _series(figs, c):
    axis = c.get("axis", "any")
    wants = c.get("y_ranges") or [c.get("y_range")]
    for fi, pi, ln in all_lines(figs, axis):
        if c.get("x_range") and not range_ok(ln["x_range"], c["x_range"], c.get("tol", 0.03)):
            continue
        if wants != [None] and not any(range_ok(ln["y_range"], w, c.get("tol", 0.03), c.get("abs", False)) for w in wants):
            continue
        return True, ""
    seen = [(ln["axis"], [round(v, 3) for v in ln["y_range"] or []]) for _, _, ln in all_lines(figs)]
    return False, f"no {axis} line with y {c.get('y_range')} (x {c.get('x_range')}); lines: {seen[:6]}"


def _series_set(figs, c):
    """Every range drawn as its own line on `axis`; same_figure: all in one figure; only: nothing else."""
    axis = c.get("axis", "y1")
    wants = c["ranges"]
    tol = c.get("tol", 0.03)
    groups = [list(all_lines([f], axis)) for f in figs] if c.get("same_figure") else [list(all_lines(figs, axis))]
    for lines in groups:
        used, ok = set(), True
        for w in wants:
            hit = next((i for i, (_, _, ln) in enumerate(lines)
                        if i not in used and range_ok(ln["y_range"], w, tol, c.get("abs", False))), None)
            if hit is None:
                ok = False
                break
            used.add(hit)
        if ok:
            if c.get("only"):
                extra = [ln["y_range"] for i, (_, _, ln) in enumerate(lines) if i not in used
                         and not any(range_ok(ln["y_range"], w, tol, c.get("abs", False)) for w in wants)]
                if extra:
                    return False, f"also drew other {axis} data: {extra[:3]}"
            return True, ""
    return False, f"{axis} lines {[ [round(v, 2) for v in ln['y_range']] for _, _, ln in all_lines(figs, axis)][:6]} " \
                  f"do not cover {wants}" + (" in one figure" if c.get("same_figure") else "")


def _only(figs, c):
    """Every data line on `axis` (all figures) matches one of the allowed ranges."""
    axis, tol = c.get("axis", "y1"), c.get("tol", 0.03)
    bad = [ln["y_range"] for _, _, ln in all_lines(figs, axis)
           if not any(range_ok(ln["y_range"], w, tol, c.get("abs", False)) for w in c["ranges"])]
    return (not bad), (f"other {axis} data drawn too: {bad[:3]}" if bad else "")


def _axis(figs, c):
    which = c.get("which", "x")
    fails = []
    for fi, f in enumerate(data_figs(figs)):
        panels = f["panels"] if c.get("panel") is None else [f["panels"][c["panel"]]] if len(f["panels"]) > c["panel"] else []
        for pi, p in enumerate(panels[:1] if c.get("panel") is None else panels):
            a = p.get(which)
            if a is None:
                fails.append(f"fig {fi}: no {which} axis")
                continue
            span = abs((a["max"] or 0) - (a["min"] or 0)) or 1.0
            for k, v in c.items():
                if k in ("which", "panel", "cat", "tol"):
                    continue
                got = a.get(k)
                if k in ("min", "max"):
                    ok = close(got, v, c.get("tol", 0.005) * span + 1e-9)
                elif k == "step":
                    ok = got is not None and abs(got - v) <= 1e-6 * max(abs(v), 1)
                elif k in ("label_size", "tick_size"):
                    ok = size_ok(got, v, f)
                elif k in ("label_color", "tick_color"):
                    ok = color_ok(got, v)
                elif k == "label":
                    ok = norm(got) == norm(v)
                elif k == "label_contains":
                    ok = norm(v) in norm(a.get("label"))
                elif k == "minor":
                    ok = bool(got) == bool(v)
                elif k == "starts_at":
                    ticks = sorted(a.get("ticks") or [])
                    ok = bool(ticks) and close(ticks[0], v, 1e-6 * max(abs(v), 1)) and close(a["min"], v, 0.01 * span)
                else:
                    ok = got == v
                if not ok:
                    fails.append(f"fig {fi}: {which}.{k} is {got!r}, want {v!r}")
    return (not fails), "; ".join(fails[:4])


def _lines(figs, c):
    axis = c.get("axis", "y1")
    lines = list(all_lines(data_figs(figs), axis))
    if not lines:
        return False, f"no {axis} line"
    fails = []
    for fi, pi, ln in lines:
        for k, v in c.items():
            if k in ("axis", "cat"):
                continue
            got = ln.get(k)
            if k == "color":
                ok = any(color_ok(got, x) for x in (v if isinstance(v, list) else [v]))
            else:
                ok = close(got, v, 0.3) if k == "width" else got == v
            if not ok:
                fails.append(f"{axis} line {k} is {got!r}, want {v!r}")
    return (not fails), "; ".join(sorted(set(fails))[:3])


def _no_y2(figs, c):
    bad = [fi for fi, f in enumerate(data_figs(figs)) for p in f["panels"] if p.get("y2") or any(l["axis"] == "y2" for l in p["lines"])]
    return (not bad), ("a right y axis is drawn" if bad else "")


def _title(figs, c):
    fails = []
    for fi, f in enumerate(data_figs(figs)):
        t = f.get("title")
        if c.get("none"):
            if t and t["text"].strip():
                fails.append(f"title {t['text']!r} shown")
            continue
        if not t:
            fails.append("no title")
            continue
        if "text" in c and norm(t["text"]) != norm(c["text"]):
            fails.append(f"title {t['text']!r}")
        if "contains" in c and norm(c["contains"]) not in norm(t["text"]):
            fails.append(f"title {t['text']!r} lacks {c['contains']!r}")
        if "size" in c and not size_ok(t["size"], c["size"], f):
            fails.append(f"title size {t['size']}")
        if "color" in c and not color_ok(t["color"], c["color"]):
            fails.append(f"title color {t['color']}")
    return (not fails), "; ".join(fails[:3])


def _legend(figs, c):
    fails = []
    for fi, f in enumerate(data_figs(figs)):
        lg = f["legend"]
        if "shown" in c and lg["shown"] != c["shown"]:
            fails.append(f"legend shown={lg['shown']}")
            continue
        if not lg["shown"]:
            if any(k in c for k in ("where", "size", "inside")):
                fails.append("no legend")
            continue
        if "where" in c and lg.get("where") != c["where"]:
            fails.append(f"legend at {lg.get('where')}")
        if "inside" in c and lg.get("inside") != c["inside"]:
            fails.append(f"legend inside={lg.get('inside')}")
        if "size" in c and not size_ok(lg.get("size"), c["size"], f):
            fails.append(f"legend size {lg.get('size')}")
    return (not fails), "; ".join(fails[:3])


def _grid(figs, c):
    bad = [fi for fi, f in enumerate(data_figs(figs)) if bool(f["panels"] and f["panels"][0]["grid"]) != c["grid"]]
    return (not bad), (f"grid is {not c['grid']}" if bad else "")


def _text_value(figs, c):
    v, tol = c["value"], c.get("tol", 0.1)
    rx = re.compile(c["regex"]) if c.get("regex") else None
    found = []
    for t in plot_texts(figs):
        if any(abs(abs(n) - v) <= tol for n in nums(t["text"])):
            found.append(t["text"])
            if rx is None or rx.search(t["text"].strip()):
                return True, ""
    if found:
        return False, f"value {v} shown as {found[:2]}, not matching {c.get('regex')}"
    return False, f"no label showing {v}±{tol}; texts: {[t['text'] for t in plot_texts(figs)][:6]}"


def _no_text_value(figs, c):
    v, tol = c["value"], c.get("tol", 5)
    hit = [t["text"] for t in plot_texts(figs) if any(abs(abs(n) - v) <= tol for n in nums(t["text"]))]
    return (not hit), (f"still shows {hit[:2]}" if hit else "")


def _text_values(figs, c):
    tol = c.get("tol", 5)
    miss = [v for v in c["values"] if not any(abs(abs(n) - v) <= tol for t in plot_texts(figs) for n in nums(t["text"]))]
    return (not miss), (f"no label for {miss}; texts: {[t['text'] for t in plot_texts(figs)][:6]}" if miss else "")


def _text_contains(figs, c):
    want = norm(c["text_contains"] if "text_contains" in c else c["text"])
    return any(want in norm(s) for s in every_text(figs)), f"no text containing {c.get('text_contains')!r}"


def _vline(figs, c):
    tol = c.get("tol", 2)
    for f in figs:
        for p in f["panels"]:
            if any(close(v["x"], c["x"], tol) for v in p["vlines"]):
                return True, ""
    return False, f"no vertical line at {c['x']}"


def _hline(figs, c):
    tol = c.get("tol", 0.5)
    for f in figs:
        for p in f["panels"]:
            if any(close(h["y"], c["y"], tol) and (c.get("axis") in (None, h["axis"])) for h in p["hlines"]):
                return True, ""
    return False, f"no horizontal line at {c['y']}"


def _span(figs, c):
    tol = c.get("tol", 3)
    for f in figs:
        for p in f["panels"]:
            for s in p["spans"]:
                if close(s["x_min"], c["x_min"], tol) and close(s["x_max"], c["x_max"], tol):
                    if c.get("color") and not color_ok(s.get("color"), c["color"]):
                        continue
                    return True, ""
    got = [(round(s["x_min"]), round(s["x_max"])) for f in figs for p in f["panels"] for s in p["spans"]]
    return False, f"no shaded {c['x_min']}–{c['x_max']}; spans: {got[:4]}"


def _spans(figs, c):
    miss = [s for s in c["spans"] if not _span(figs, {"x_min": s[0], "x_max": s[1], "tol": c.get("tol", 15)})[0]]
    return (not miss), (f"missing shaded ranges {miss}" if miss else "")


def _text_color(figs, c):
    cols = []
    for f in data_figs(figs):
        if f.get("title"):
            cols.append(f["title"]["color"])
        p = f["panels"][0] if f["panels"] else None
        if p:
            for ax in ("x", "y1", "y2"):
                if p.get(ax):
                    cols += [p[ax]["label_color"], p[ax]["tick_color"]]
        cols += f["legend"].get("colors") or []
    cols = [x for x in cols if x]
    ok = sum(color_ok(x, c["text_color"]) for x in cols)
    return (cols and ok / len(cols) >= 0.9), f"{ok}/{len(cols)} texts are {c['text_color']}"


def _font_size(figs, c):
    v = c["font_size"]
    got, ok = [], True
    for f in data_figs(figs):
        p = f["panels"][0]
        sizes = [p["x"]["label_size"], p["x"]["tick_size"], p["y1"]["label_size"]]
        got += sizes
        ok = ok and all(size_ok(g, v, f) for g in sizes if g is not None)
    ok = bool(got) and ok
    return bool(ok), f"axis text sizes {sorted(set(round(g, 1) for g in got if g))}"


def _png_px(figs, c):
    w, h = c["png_px"]
    pxs = [e["px"] for f in figs for e in f["files"] if e.get("px")]
    return any(abs(p[0] - w) <= 3 and abs(p[1] - h) <= 3 for p in pxs), f"png sizes {pxs[:3]}"


def _formats(figs, c):
    have = {e["format"] for f in figs for e in f["files"] if e.get("exists", True)}
    miss = [x for x in c["formats"] if x not in have]
    return (not miss), (f"missing {miss}; saved {sorted(have)}" if miss else "")


def _figures(figs, c):
    n = len(data_figs(figs)) if figs else 0
    ok = n >= c.get("min", 0) and n <= c.get("max", 10 ** 6)
    return ok, f"{n} figures"


def _panels(figs, c):
    n = max((len(f["panels"]) for f in figs), default=0)
    return n >= c.get("min", 1) and n <= c.get("max", 99), f"{n} panels"


def _visible(figs, c):
    """Data on `axis` mostly inside the axis range (a wrong sign or range hides it)."""
    bad = []
    for f in data_figs(figs):
        for p in f["panels"]:
            a = p.get(c.get("axis", "y1"))
            for ln in p["lines"]:
                if ln["axis"] != c.get("axis", "y1") or not a or not ln["y_range"]:
                    continue
                lo, hi = ln["y_range"]
                inter = max(0.0, min(hi, a["max"]) - max(lo, a["min"]))
                if (hi - lo) > 0 and inter / (hi - lo) < c.get("frac", 0.8):
                    bad.append([round(lo, 3), round(hi, 3)])
    return (not bad), (f"{c.get('axis')} data {bad[:2]} mostly outside the axis range" if bad else "")


def _offset(figs, c):
    """Combined curves shifted from each other: the y1 lines' starting levels differ by about `step`."""
    for f in figs:
        tops = sorted(ln["y_range"][1] for p in f["panels"] for ln in p["lines"] if ln["axis"] == "y1")
        if len(tops) >= c.get("n", 2):
            d = np.diff(tops)
            if len(d) and np.min(np.abs(d)) >= c.get("min_gap", 5):
                return True, ""
    return False, "curves are not offset"


def _fill(figs, c):
    n = sum(p["fills"] for f in figs for p in f["panels"])
    return n >= c.get("min", 1), f"{n} filled areas"


def _size_in(figs, c):
    got = [f["size_in"] for f in data_figs(figs)]
    ok = got and all((c.get("w") is None or close(g[0], c["w"], c.get("tol", 0.05)))
                     and (c.get("h") is None or close(g[1], c["h"], c.get("tol", 0.05))) for g in got)
    return bool(ok), f"figure sizes {got[:3]}"


def _line_color(figs, c):
    for _, _, ln in all_lines(figs, c.get("axis", "y1")):
        if range_ok(ln["y_range"], c["y_range"], c.get("tol", 0.03)):
            return color_ok(ln["color"], c["color"]), f"that line is {ln['color']}, want {c['color']}"
    return False, f"no line with y {c['y_range']}"


def _any_of(figs, c):
    """Passes when any of the alternative checks passes (requests with more than one fair reading)."""
    whys = []
    for alt in c["any_of"]:
        kind = next(k for k in alt if k in CHECKS)
        ok, why = CHECKS[kind](figs, alt[kind] if isinstance(alt[kind], dict) else alt)
        if ok:
            return True, ""
        whys.append(why)
    return False, " / ".join(whys)


CHECKS = {"series": _series, "series_set": _series_set, "only": _only, "axis": _axis, "lines": _lines,
          "no_y2": _no_y2, "title": _title, "legend": _legend, "grid": _grid, "text_value": _text_value,
          "no_text_value": _no_text_value, "text_values": _text_values, "text_contains": _text_contains,
          "vline": _vline, "hline": _hline, "span": _span, "spans": _spans, "text_color": _text_color,
          "font_size": _font_size, "png_px": _png_px, "formats": _formats, "figures": _figures,
          "panels": _panels, "visible": _visible, "offset": _offset, "fill": _fill, "size_in": _size_in,
          "line_color": _line_color, "any_of": _any_of}


def run_checks(figs, checks):
    results = []
    for c in checks:
        kind = next(k for k in c if k in CHECKS)
        arg = c[kind] if isinstance(c[kind], dict) else c
        try:
            ok, why = CHECKS[kind](figs, arg)
        except Exception as e:                      # a malformed figure must fail, not crash the run
            ok, why = False, f"check error: {e!r}"
        results.append({"check": kind, "cat": c.get("cat", "ask"), "ok": bool(ok), "why": "" if ok else why,
                        "spec": c})
    return all(r["ok"] for r in results), results
