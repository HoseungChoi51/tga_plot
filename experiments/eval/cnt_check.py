"""Check one turn of a CNT request: the chart facts of what was drawn against the turn's expectation
(eval/cnt/<split>/requests.json, written by an independent test author; conventions in its "meta").

    check(expect, facts, result, spec) -> {"pass", "n_checks", "n_failed", "failed": [...], "unchecked": [...],
                                           "kind_expected", "figure"}

Series and categories are matched by content, not by label text. Tolerances follow the meta:
aggregates abs <= max(0.5 % of |value|, 0.01); ranges abs <= max(0.5 %, 0.05); pie shares 0.2 percentage points;
counts exact (scatter/line point counts within 1 % or 2 points, since a renderer may drop NaN rows);
computed asks use their own "tol".
"""
import math
import re
from datetime import datetime

import numpy as np

AGG_TOL = (0.005, 0.01)
RNG_TOL = (0.005, 0.05)
SHARE_TOL_PP = 0.2


def _close(a, b, rel_abs=AGG_TOL):
    if a is None or b is None:
        return False
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    rel, ab = rel_abs
    return abs(a - b) <= max(rel * abs(b), ab)


def _num(v):
    try:
        f = float(str(v).replace(",", "").replace("−", "-").strip())
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _date_num(v):
    """A date/time (string, ms epoch, or matplotlib day number) -> days since epoch."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if v > 1e11:            # ms since epoch (ECharts time axis)
            return v / 86400e3
        return float(v)         # matplotlib date number (days since 1970)
    s = str(v).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s[:19] if "%S" in fmt else s[:len(datetime.now().strftime(fmt))], fmt)
            return (d - datetime(1970, 1, 1)).total_seconds() / 86400
        except ValueError:
            continue
    return None


def _xnum(v):
    n = _num(v)
    if n is not None and not (isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}", v)):
        return n / 86400e3 if n > 1e11 else n          # ECharts time values are milliseconds
    return _date_num(v)


def norm_label(s):
    s = str(s).strip().lower()
    s = s.replace("−", "-").replace("–", "-").replace("~", "-")
    s = re.sub(r"\s+", "", s)
    n = _num(s)
    if n is not None:
        return f"{n:g}"
    return s


# ---------------------------------------------------------------- matching categories
def _cat_variants(lab):
    """Ways a drawn category label may write an expected one (dates -> month, week, day; numbers; no unit)."""
    out = {norm_label(lab)}
    s = str(lab).strip()
    base = re.sub(r"\s*[\(\[][^()\[\]]*[\)\]]\s*$", "", s)
    if base and base != s:
        out.add(base)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        out |= {str(mo), f"{mo}월", f"{y}-{mo:02d}", f"{y}-{mo}", f"{mo:02d}", f"{y}{mo:02d}", f"{y}/{mo:02d}",
                f"{mo}/{d}", f"{mo:02d}-{d:02d}", s[:10]}
        try:
            wk = datetime(y, mo, d).isocalendar()[1]
            out |= {str(wk), f"w{wk}", f"w{wk:02d}", f"{wk}주", f"week{wk}"}
        except ValueError:
            pass
    m = re.match(r"^(\d+)\s*(월|주|주차|week|wk|w)$", s.lower())
    if m:
        out.add(m.group(1))
    m = re.match(r"^(w|week|wk)\s*(\d+)$", s.lower())
    if m:
        out.add(str(int(m.group(2))))
    m = re.match(r"^([-\d.]+)\s*[-–~]\s*([-\d.]+)$", s)       # bins "2.5–3.0" vs "2.5–3"
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        if a is not None and b is not None:
            out |= {f"{a:g}-{b:g}", f"({a:g},{b:g}]", f"[{a:g},{b:g})", f"{a:g}~{b:g}"}
    m = re.match(r"^[\[(]\s*([-\d.]+)\s*,\s*([-\d.]+)\s*[\])]$", s)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        out |= {f"{a:g}-{b:g}"}
    return {norm_label(v) for v in out}


def match_categories(expected, drawn):
    """{expected label: index in drawn} for the labels that can be matched."""
    exp_n = {e: norm_label(e) for e in expected}
    var = [(_cat_variants(d)) for d in drawn]
    out = {}
    used = set()
    for e, en in exp_n.items():
        for i, v in enumerate(var):
            if i not in used and en in v:
                out[e] = i
                used.add(i)
                break
    return out


# ---------------------------------------------------------------- facts helpers
def _panels(f):
    return f.get("panels") or []


def _all_lines(f):
    return [l for p in _panels(f) for l in p["lines"]]


def _all_points(f):
    return [q for p in _panels(f) for q in p["points"]]


def _all_bars(f):
    return [b for p in _panels(f) for b in p["bars"]]


def _all_hist(f):
    return [h for p in _panels(f) for h in p["hist"]]


def _texts(f):
    t = list(f.get("texts") or [])
    for p in _panels(f):
        t += p.get("texts") or []
        for ax in ("x", "y"):
            if p.get(ax):
                t.append(p[ax].get("label") or "")
    t += (f.get("legend") or {}).get("entries") or []
    if f.get("title"):
        t.append(f["title"])
    return [str(x) for x in t if x]


def _numbers_in(texts):
    out = []
    for t in texts:
        for m in re.finditer(r"[-−]?\d[\d,]*\.?\d*(?:[eE][-+]?\d+)?", t):
            n = _num(m.group(0).replace(",", ""))
            if n is not None:
                out.append(n)
    return out


def kind_of(f):
    kinds = set()
    for p in _panels(f):
        if p.get("pie"):
            kinds.add("pie")
        if p.get("heatmap"):
            kinds.add("heatmap")
        if p["hist"]:
            kinds.add("histogram")
        if p["bars"]:
            bars = p["bars"]
            orient = bars[0]["orient"]
            stacked = len(bars) > 1 and any(any(abs(v or 0) > 1e-9 for v in b["bottoms"]) for b in bars[1:])
            if len(bars) > 1:
                kinds.add("stacked_bar" if stacked else "grouped_bar")
            kinds.add("hbar" if orient == "h" else "bar")
        if [q for q in p["points"] if q["n"] >= 3]:
            kinds.add("scatter")
        if [l for l in p["lines"] if l["n"] >= 3]:
            kinds.add("line")
    return kinds


KIND_OK = {
    "bar": {"bar", "hbar"}, "hbar": {"hbar"}, "grouped_bar": {"grouped_bar"}, "stacked_bar": {"stacked_bar"},
    "line": {"line"}, "scatter": {"scatter"}, "histogram": {"histogram"}, "heatmap": {"heatmap"}, "pie": {"pie"},
}


# ---------------------------------------------------------------- per-kind value checks
def _bar_table(f):
    """[(series name, {category label: value}, orient, bottoms)] from the drawn bars."""
    out = []
    for b in _all_bars(f):
        out.append((b["name"], list(b["cats"]), b["values"], b["orient"]))
    return out


def check_bar(e, f, fails, notes, scale=1.0):
    v = e.get("values") or {}
    vals = v.get("values") or {}
    bars = _bar_table(f)
    if not bars:
        fails.append("values: no bars drawn")
        return
    # a single series: pick the drawn series that matches best
    best = None
    for name, cats, ys, orient in bars:
        m = match_categories(list(vals), cats)
        good = sum(1 for k, i in m.items() if _close(ys[i] * scale if ys[i] is not None else None, vals[k]))
        if best is None or good > best[0]:
            best = (good, name, cats, ys, m)
    good, name, cats, ys, m = best
    missing = [k for k in vals if k not in m]
    wrong = [f"{k}: drawn {'none' if ys[m[k]] is None else format(ys[m[k]], '.4g')}, want {vals[k]:.4g}" for k in vals
             if k in m and not _close(ys[m[k]] * scale if ys[m[k]] is not None else None, vals[k])]
    if missing:
        fails.append(f"values: categories not drawn: {missing[:6]} (drawn: {cats[:8]})")
    if wrong:
        fails.append("values: " + "; ".join(wrong[:5]))
    extra = [c for i, c in enumerate(cats) if i not in m.values() and ys[i] not in (None, 0)]
    if extra and len(extra) > 0.2 * max(1, len(vals)):
        fails.append(f"values: extra categories drawn: {extra[:6]}")
    if (e.get("data") or {}).get("sort") and v.get("order") and not missing:
        order = sorted(m, key=lambda k: m[k])
        if order != [k for k in v["order"] if k in m]:
            fails.append(f"order: drawn {order[:8]}, want {v['order'][:8]}")


def check_grouped(e, f, fails, notes, stacked, scale=1.0):
    v = e.get("values") or {}
    table = v.get("values") or {}
    xs = list(v.get("x") or table.keys())
    series = list(v.get("series") or sorted({s for d in table.values() for s in d}))
    bars = _all_bars(f)
    if len(bars) < 2:
        fails.append(f"values: {len(bars)} bar series drawn, want {len(series)}")
        return
    # match series by name first, then by content
    remaining = list(range(len(bars)))
    assign = {}
    for s in series:
        hit = [i for i in remaining if norm_label(bars[i]["name"]) == norm_label(s)]
        if hit:
            assign[s] = hit[0]
            remaining.remove(hit[0])

    def score(s, i):
        m = match_categories(xs, bars[i]["cats"])
        return sum(1 for x, k in m.items() if _close((bars[i]["values"][k] or 0) * scale, table.get(x, {}).get(s, 0)))
    for s in series:
        if s in assign:
            continue
        if not remaining:
            break
        i = max(remaining, key=lambda i: score(s, i))
        assign[s] = i
        remaining.remove(i)
    wrong, missing = [], []
    for s in series:
        if s not in assign:
            missing.append(s)
            continue
        b = bars[assign[s]]
        m = match_categories(xs, b["cats"])
        for x in xs:
            want = table.get(x, {}).get(s)
            if want is None:
                continue
            if x not in m:
                if abs(want) > 1e-9:
                    missing.append(f"{x}/{s}")
                continue
            got = b["values"][m[x]]
            if not _close((got or 0) * scale, want):
                wrong.append(f"{x}/{s}: drawn {got}, want {want}")
    if missing:
        fails.append(f"values: not drawn: {missing[:6]}")
    if wrong:
        fails.append("values: " + "; ".join(wrong[:5]))
    is_stacked = any(any(abs(v_ or 0) > 1e-9 for v_ in b["bottoms"]) for b in bars[1:])
    if stacked and not is_stacked:
        fails.append("kind: bars are side by side, want stacked")
    if not stacked and is_stacked:
        fails.append("kind: bars are stacked, want side by side")


def _series_match(exp_series, drawn, getn, getrng, xr_key="x_range"):
    """Assign expected series to drawn ones by n and y range."""
    remaining = list(range(len(drawn)))
    assign = {}
    for name, d in exp_series.items():
        best, bs = None, -1
        for i in remaining:
            l = drawn[i]
            s = 0
            if norm_label(l.get("name", "")) == norm_label(name):
                s += 1
            n = getn(l)
            if d.get("n") is not None and n is not None and abs(n - d["n"]) <= max(2, 0.01 * d["n"]):
                s += 2
            yr = getrng(l)
            if d.get("y_range") and yr and _close(yr[0], d["y_range"][0], RNG_TOL) and _close(yr[1], d["y_range"][1], RNG_TOL):
                s += 3
            if s > bs:
                best, bs = i, s
        if best is not None:
            assign[name] = best
            remaining.remove(best)
    return assign


def _window(e, f):
    """An xlim ask met by the axis: (lo, hi) of what is in view, to judge the series by what the reader sees."""
    ask = next((a for a in e.get("asks") or [] if str(a.get("what", "")).lower() == "xlim" and isinstance(a.get("value"), list)), None)
    if not ask:
        return None
    lo, hi = _xnum(ask["value"][0]), _xnum(ask["value"][1])
    ax = (_panels(f)[0] if _panels(f) else {}).get("x") or {}
    glo, ghi = _xnum(ax.get("min")), _xnum(ax.get("max"))
    if None in (lo, hi, glo, ghi):
        return None
    span = abs(hi - lo) or 1
    return (glo, ghi) if abs(glo - lo) <= 0.01 * span and abs(ghi - hi) <= 0.01 * span else None


def check_line(e, f, fails, notes):
    v = e.get("values") or {}
    series = v.get("series") or {}
    lines = [l for l in _all_lines(f) if l["n"] >= 3]
    win = _window(e, f)
    if win:                                    # zoomed with the axis: only the points in view count
        cut = []
        for l in lines:
            keep = [(x, y) for x, y in zip(l["x"], l["y"]) if _xnum(x) is not None and win[0] - 1e-9 <= _xnum(x) <= win[1] + 1e-9]
            cut.append({**l, "x": [k[0] for k in keep], "y": [k[1] for k in keep], "n": len(keep)})
        lines = [l for l in cut if l["n"] >= 3]
        notes.append("zoomed by the axis: points outside the view are not counted")
    want_n = v.get("n_series") or len(series)
    if len(lines) < want_n:
        fails.append(f"lines: {len(lines)} drawn, want {want_n}")
    def yr(l):
        ys = [y for y in l["y"] if y is not None]
        return [min(ys), max(ys)] if ys else None
    assign = _series_match(series, lines, lambda l: sum(1 for y in l["y"] if y is not None), yr)
    for name, d in series.items():
        if name not in assign:
            fails.append(f"series {name}: not drawn")
            continue
        l = lines[assign[name]]
        n = sum(1 for y in l["y"] if y is not None)
        if d.get("n") is not None and abs(n - d["n"]) > max(2, 0.01 * d["n"]):
            fails.append(f"series {name}: {n} points, want {d['n']}")
        r = yr(l)
        if d.get("y_range") and r and not (_close(r[0], d["y_range"][0], RNG_TOL) and _close(r[1], d["y_range"][1], RNG_TOL)):
            fails.append(f"series {name}: y range {r[0]:.4g}..{r[1]:.4g}, want {d['y_range'][0]:.4g}..{d['y_range'][1]:.4g}")
        if d.get("points") and len(d["points"]) <= 60:
            xs = _x_like(l["x"], [p_[0] for p_ in d["points"]])
            bad = 0
            for px, py in d["points"]:
                pxn = _xnum(px)
                cand = [(abs((x or 0) - pxn), y) for x, y in zip(xs, l["y"]) if x is not None and y is not None] if pxn is not None else []
                if not cand:
                    continue
                dx, y = min(cand, key=lambda t: t[0])
                if not _close(y, py):
                    bad += 1
            if bad:                          # the same values in order, on another x scale (dates for week numbers)
                drawn = [y for x, y in sorted(((x, y) for x, y in zip(xs, l["y"]) if x is not None and y is not None), key=lambda t: t[0])]
                want = [py for px, py in sorted(d["points"], key=lambda t: _xnum(t[0]) or 0)]
                if len(drawn) == len(want) and all(_close(a, b) for a, b in zip(drawn, want)):
                    notes.append(f"series {name}: same values in order on another x scale")
                    bad = 0
            if bad:
                fails.append(f"series {name}: {bad} of {len(d['points'])} points off")


def _x_like(drawn, expected):
    """The drawn x values in the form the expectation uses: dates may stand for months (3..12) or ISO weeks."""
    xs = [_xnum(x) for x in drawn]
    ex = [_xnum(x) for x in expected]
    if not xs or not ex or any(v is None for v in ex):
        return xs
    is_dates = all(v is not None and v > 3000 for v in xs)          # days since 1970
    if not is_dates or not all(0 < v <= 53 and float(v).is_integer() for v in ex):
        return xs
    from datetime import datetime, timedelta
    days = [datetime(1970, 1, 1) + timedelta(days=v) for v in xs]
    cands = {"month": [float(d.month) for d in days], "week": [float(d.isocalendar()[1]) for d in days]}
    best = max(cands.values(), key=lambda c: sum(1 for v in ex if v in c))
    return best


def check_scatter(e, f, fails, notes, alts):
    v = e.get("values") or {}
    pts = [q for q in _all_points(f) if q["n"] >= 3]
    if not pts:
        fails.append("scatter: no points drawn")
        return
    n = sum(q["n"] for q in pts)
    if v.get("n") is not None and abs(n - v["n"]) > max(2, 0.01 * v["n"]):
        fails.append(f"scatter: {n} points, want {v['n']}")
    xs = [x for q in pts for x in (q.get("x") or [])]
    ys = [y for q in pts for y in (q.get("y") or [])]
    xr = [min(q["x_range"][0] for q in pts if q["x_range"]), max(q["x_range"][1] for q in pts if q["x_range"])] if any(q["x_range"] for q in pts) else None
    yr = [min(q["y_range"][0] for q in pts if q["y_range"]), max(q["y_range"][1] for q in pts if q["y_range"])] if any(q["y_range"] for q in pts) else None

    def rng_ok(got, want):
        return got and want and _close(got[0], want[0], RNG_TOL) and _close(got[1], want[1], RNG_TOL)
    swap_ok = any(("바뀐" in a or "swap" in a.lower() or "x/y" in a.lower()) for a in alts)
    want_x, want_y = v.get("x_range"), v.get("y_range")
    straight = (not want_x or rng_ok(xr, [_xnum(want_x[0]), _xnum(want_x[1])])) and (not want_y or rng_ok(yr, want_y))
    swapped = swap_ok and (not want_x or rng_ok(yr, [_xnum(want_x[0]), _xnum(want_x[1])])) and (not want_y or rng_ok(xr, want_y))
    if not (straight or swapped):
        fails.append(f"scatter: ranges x {xr} y {yr}, want x {want_x} y {want_y}")
    if v.get("pearson_r") is not None and xs and len(xs) == len(ys):
        a, b = np.asarray(xs, dtype=float), np.asarray([y if y is not None else np.nan for y in ys], dtype=float)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() > 3:
            r = float(np.corrcoef(a[ok], b[ok])[0, 1])
            if abs(r - v["pearson_r"]) > 0.02:
                fails.append(f"scatter: r = {r:.3f}, want {v['pearson_r']:.3f}")
    if isinstance(v.get("series"), dict) and len(v["series"]) > 1:
        want = sorted(v["series"].values())
        by_col = {}
        for q in pts:                         # two groups in one colour look like one group
            by_col[q.get("color")] = by_col.get(q.get("color"), 0) + q["n"]
        got = sorted(by_col.values()) if len(by_col) == len(want) else sorted(q["n"] for q in pts)
        multi_col = [q for q in pts if q.get("colors") and len(q["colors"]) >= len(want)]
        if got != want and not (len(pts) == 1 and multi_col):
            fails.append(f"scatter: groups of {got} points, want {want}")


def check_hist(e, f, fails, notes):
    v = e.get("values") or {}
    hs = _all_hist(f)
    if not hs:
        bars = _all_bars(f)
        if bars:     # a histogram drawn as bars over bin labels
            hs = [{"name": b["name"], "counts": b["values"], "edges": None} for b in bars]
        else:
            fails.append("histogram: no bars drawn")
            return
    total = sum(sum(c or 0 for c in h["counts"]) for h in hs)
    if v.get("n") is not None and abs(total - v["n"]) > 0.5 and not _close(total, 1.0, (0, 0.05)):
        fails.append(f"histogram: {total:g} values counted, want {v['n']}")
    groups = v.get("by") or ({"_": {"n": v.get("n"), "bins": v.get("bins")}} if v.get("bins") else {})
    for g, d in groups.items():
        b = d.get("bins") if isinstance(d, dict) else None
        if not b:
            continue
        cand = [h for h in hs if h.get("edges")]
        hit = None
        for h in cand:
            if len(h["counts"]) == len(b["counts"]) and all(abs((x or 0) - y) <= 0.5 for x, y in zip(h["counts"], b["counts"])):
                hit = h
            elif h.get("edges") and _same_bins(h, b):
                hit = h
        if hit is None:
            ok_edges = [h for h in cand if h["edges"] and len(h["edges"]) == len(b["edges"]) and
                        all(_close(x, y, RNG_TOL) for x, y in zip(h["edges"], b["edges"]))]
            fails.append(f"histogram {g}: bins/counts differ" + ("" if ok_edges else " (edges differ)"))


def _same_bins(h, b):
    """Drawn and expected bins agree on every shared bin, and bins only one side has are empty."""
    def table(edges, counts):
        return {round(float(lo), 6): (round(float(hi), 6), c or 0) for lo, hi, c in zip(edges, edges[1:], counts)}
    d, w = table(h["edges"], h["counts"]), table(b["edges"], b["counts"])
    for lo in set(d) | set(w):
        if lo in d and lo in w:
            if d[lo][0] != w[lo][0] or abs(d[lo][1] - w[lo][1]) > 0.5:
                return False
        elif (d.get(lo) or w.get(lo))[1] > 0.5:
            return False
    return bool(set(d) & set(w))


def check_heatmap(e, f, fails, notes):
    v = e.get("values") or {}
    hm = next((p["heatmap"] for p in _panels(f) if p.get("heatmap")), None)
    if hm is None:
        fails.append("heatmap: none drawn")
        return
    rows, cols, mat = v.get("rows") or [], v.get("cols") or [], v.get("matrix") or []
    for transpose in (False, True):
        R, C = (hm["rows"], hm["cols"]) if not transpose else (hm["cols"], hm["rows"])
        rm, cm = match_categories(rows, [str(x) for x in R]), match_categories(cols, [str(x) for x in C])
        if len(rm) >= 0.8 * len(rows) and len(cm) >= 0.8 * len(cols):
            bad, n = 0, 0
            for i, r in enumerate(rows):
                for j, c in enumerate(cols):
                    if r not in rm or c not in cm:
                        continue
                    got = hm["z"][rm[r]][cm[c]] if not transpose else hm["z"][cm[c]][rm[r]]
                    want = mat[i][j] if i < len(mat) and j < len(mat[i]) else None
                    if want is None:
                        continue
                    n += 1
                    if not _close(got, want):
                        bad += 1
            if len(rm) < len(rows) or len(cm) < len(cols):
                fails.append(f"heatmap: {len(rows) - len(rm)} rows / {len(cols) - len(cm)} columns missing")
            if bad:
                fails.append(f"heatmap: {bad} of {n} cells off")
            return
    fails.append(f"heatmap: rows/columns differ (drawn {hm['rows'][:5]} x {hm['cols'][:5]}, want {rows[:5]} x {cols[:5]})")


def check_pie(e, f, fails, notes, scale=1.0):
    v = e.get("values") or {}
    pie = next((p["pie"] for p in _panels(f) if p.get("pie")), None)
    if pie is None:
        fails.append("pie: none drawn")
        return
    want = v.get("shares_pct") or {}
    if not want and v.get("values"):
        tot = sum(v["values"].values())
        want = {k: 100 * x / tot for k, x in v["values"].items()}
    labels = [l or "" for l in pie["labels"]]
    m = match_categories(list(want), labels)
    if len(m) < len(want):
        # maybe the labels are not readable (raw code): match by share alone
        got = sorted(100 * s for s in pie["shares"])
        exp = sorted(want.values())
        if len(got) == len(exp) and all(abs(a - b) <= SHARE_TOL_PP for a, b in zip(got, exp)):
            notes.append("pie: labels not matched, shares match")
            return
        fails.append(f"pie: slices {labels[:8]}, want {list(want)[:8]}")
        return
    wrong = [f"{k}: {100 * pie['shares'][i]:.2f}%, want {want[k]:.2f}%" for k, i in m.items()
             if abs(100 * pie["shares"][i] - want[k]) > SHARE_TOL_PP]
    if wrong:
        fails.append("pie: " + "; ".join(wrong[:5]))
    extra = [l for i, l in enumerate(labels) if i not in m.values()]
    if extra:
        fails.append(f"pie: extra slices {extra[:5]}")


# ---------------------------------------------------------------- asks
_COLORS = None


def _rgb(c):
    from matplotlib.colors import to_rgb
    try:
        return np.array(to_rgb(c))
    except (ValueError, TypeError):
        k = {"빨강": "red", "빨간색": "red", "파랑": "blue", "파란색": "blue", "초록": "green", "녹색": "green",
             "검정": "black", "회색": "gray", "주황": "orange", "보라": "purple", "노랑": "gold"}.get(str(c).strip())
        return np.array(to_rgb(k)) if k else None


def _color_like(got, want):
    a, b = _rgb(got), _rgb(want)
    if a is None or b is None:
        return False
    if np.linalg.norm(a - b) < 0.35:
        return True
    import colorsys
    ha, la, sa = colorsys.rgb_to_hls(*a)
    hb, lb, sb = colorsys.rgb_to_hls(*b)
    if sb < 0.15:                       # gray/black/white: low saturation, similar lightness
        return sa < 0.2 and abs(la - lb) < 0.35
    dh = min(abs(ha - hb), 1 - abs(ha - hb))
    return sa > 0.25 and dh < 0.08 and abs(la - lb) < 0.35


def _colors_of(f):
    """{label: [colours]} for series, categories and slices."""
    out = {}
    for p in _panels(f):
        for b in p["bars"]:
            out.setdefault(b["name"], []).extend(b["colors"])
            for c, col in zip(b["cats"], b["colors"]):
                out.setdefault(c, []).append(col)
        for l in p["lines"]:
            out.setdefault(l["name"], []).append(l["color"])
        for q in p["points"]:
            out.setdefault(q["name"], []).append(q["color"])
            for c in q.get("colors") or []:
                out.setdefault("_any", []).append(c)
        for h in p["hist"]:
            out.setdefault(h["name"], []).append(h["color"])
        if p.get("pie"):
            for l, c in zip(p["pie"]["labels"], p["pie"]["colors"]):
                out.setdefault(l or "", []).append(c)
    return out


def check_asks(asks, f, spec, fails, unchecked, scale_note):
    texts = _texts(f)
    nums = _numbers_in(texts)
    p0 = _panels(f)[0] if _panels(f) else {}
    for a in asks or []:
        w = str(a.get("what", "")).lower()
        val = a.get("value")
        if w == "computed":
            tol = a.get("tol")
            ok = any((abs(n - val) <= tol) if tol is not None else _close(n, val) for n in nums) if isinstance(val, (int, float)) else False
            if not ok and isinstance(val, (int, float)):       # a normalised curve shows the value as its max
                for l in _all_lines(f):
                    ys = [y for y in l["y"] if y is not None]
                    if ys and abs(max(ys) - val) <= (tol or 0.01):
                        ok = True
            if not ok:
                fails.append(f"computed {a.get('name', '')}: {val} not shown")
        elif w in ("colors", "colours", "color"):
            cols = _colors_of(f)
            want = val if isinstance(val, dict) else {}
            bad = []
            for k, c in want.items():
                hit = None
                for lab, cs in cols.items():
                    if norm_label(lab) == norm_label(k) or (k and norm_label(k) in norm_label(lab)):
                        hit = cs
                        break
                if hit is None and re.search(r"[/,]", str(k)):      # "A/B": every part in that colour
                    parts = [x.strip() for x in re.split(r"[/,]", str(k)) if x.strip()]
                    found = [next((cs for lab, cs in cols.items() if norm_label(lab) == norm_label(pt)), None) for pt in parts]
                    if all(found):
                        if not all(any(_color_like(x, c) for x in cs if x) for cs in found):
                            bad.append(f"{k}: not {c}")
                        continue
                if hit is None:
                    hit = cols.get("_any")
                    if hit and any(_color_like(x, c) for x in hit):
                        continue
                    bad.append(f"{k}: not found")
                elif not any(_color_like(x, c) for x in hit if x):
                    bad.append(f"{k}: {hit[:2]} not {c}")
            if bad:
                fails.append("colors: " + "; ".join(bad[:4]))
        elif w in ("legend_loc", "legend", "legend_position"):
            lg = f.get("legend") or {}
            if str(val).startswith("outside"):
                if not (lg.get("shown") and lg.get("where") == "outside"):
                    fails.append(f"legend: {lg.get('where')}, want outside")
            elif val in (None, False, "none"):
                if lg.get("shown"):
                    fails.append("legend: shown, want none")
            else:
                if not lg.get("shown"):
                    fails.append("legend: not shown")
                elif lg.get("where") and str(val) not in str(lg.get("where")):
                    fails.append(f"legend: {lg.get('where')}, want {val}")
        elif w in ("value_labels", "bar_annotations", "pct_labels", "labels"):
            want_vals = val if isinstance(val, dict) else None
            if want_vals:
                miss = [k for k, x in want_vals.items() if not any(_close(n, x) for n in nums)]
                if miss:
                    fails.append(f"{w}: values not shown for {miss[:5]}")
            else:
                n_lab = sum(p.get("value_labels", 0) for p in _panels(f)) + sum(1 for t in texts if re.fullmatch(r"\s*[-−]?[\d.,]+\s*%?\s*", t))
                pct = sum(1 for t in texts if "%" in t)
                if w == "pct_labels" and pct == 0 and not any(p.get("pie") for p in _panels(f)):
                    fails.append("pct_labels: no percent labels")
                elif w == "pct_labels" and pct == 0:
                    fails.append("pct_labels: no percent labels")
                elif w != "pct_labels" and n_lab == 0:
                    fails.append(f"{w}: no value labels")
        elif w in ("title",):
            t = f.get("title") or ""
            if norm_label(val) not in norm_label(t):
                fails.append(f"title: {t!r}, want {val!r}")
        elif w in ("xlim", "ylim"):
            ax = p0.get("x" if w == "xlim" else "y") or {}
            if p0.get("bars") and p0["bars"][0]["orient"] == "h":
                ax = p0.get("y" if w == "xlim" else "x") or {}
            lo, hi = (_xnum(val[0]), _xnum(val[1])) if isinstance(val, list) else (None, None)
            glo, ghi = _xnum(ax.get("min")), _xnum(ax.get("max"))
            if ax.get("type") == "time" and glo is not None and glo > 1e6:
                glo, ghi = glo / 86400e3, ghi / 86400e3
            if lo is None or glo is None or not (_close(glo, lo, (0.002, 0.02)) and _close(ghi, hi, (0.002, 0.02))):
                data_ok = "zoom" in str(a.get("note", "")) or "data" in str(a.get("note", ""))
                fails.append(f"{w}: {ax.get('min')}..{ax.get('max')}, want {val}" + (" (axis)" if data_ok else ""))
        elif w in ("xtick_step", "ytick_step", "tick_step"):
            ax = p0.get("y" if w.startswith("y") else "x") or {}
            st = ax.get("step")
            if not _close(st, val, (0.001, 1e-6)):
                fails.append(f"{w}: {st}, want {val}")
        elif w == "unit":
            labs = " ".join((p.get("y") or {}).get("label", "") + " " + (p.get("x") or {}).get("label", "") for p in _panels(f))
            if str(val).lower() not in labs.lower() and not (val == "h" and "시간" in labs):
                fails.append(f"unit: axis labels {labs!r} do not say {val}")
        elif w in ("colormap", "cmap"):
            hm = next((p["heatmap"] for p in _panels(f) if p.get("heatmap")), None)
            if hm is None:
                fails.append("colormap: no heatmap")
            elif str(val).lower() == "diverging":
                name = (hm.get("cmap") or "").lower()
                ramp = hm.get("ramp") or []
                div = any(k in name for k in ("rdbu", "coolwarm", "bwr", "seismic", "rdylbu", "rdylgn", "piyg", "prgn", "brbg", "puor", "spectral", "rdgy"))
                if not div and ramp:
                    mid = _rgb(ramp[len(ramp) // 2])
                    ends = [_rgb(ramp[0]), _rgb(ramp[-1])]
                    div = mid is not None and mid.mean() > 0.8 and all(e_ is not None and e_.mean() < 0.75 for e_ in ends)
                if not div:
                    fails.append(f"colormap: {name or ramp[:3]} is not diverging")
            else:
                name = (hm.get("cmap") or "").lower()
                if str(val).lower() not in name:
                    fails.append(f"colormap: {name}, want {val}")
        elif w in ("clim", "color_range"):
            hm = next((p["heatmap"] for p in _panels(f) if p.get("heatmap")), None)
            cl = (hm or {}).get("clim")
            if not cl or not (_close(cl[0], val[0], (0.01, 0.01)) and _close(cl[1], val[1], (0.01, 0.01))):
                fails.append(f"clim: {cl}, want {val}")
        else:
            unchecked.append(f"{w}={val}")


# ---------------------------------------------------------------- entry
def _scale_from_alts(alts):
    out = [1.0]
    for a in alts:
        for m in re.finditer(r"[÷/]\s*(\d+(?:\.\d+)?)", a):
            out.append(1 / float(m.group(1)))
        for m in re.finditer(r"[×x*]\s*(\d+(?:\.\d+)?)", a):
            out.append(float(m.group(1)))
    return out


def check_figure(e, f):
    fails, notes, unchecked = [], [], []
    kind = e.get("kind")
    alts = [str(a) for a in e.get("alternatives") or []]
    drawn = kind_of(f)
    if kind in KIND_OK and not (drawn & KIND_OK[kind]):
        alt_kind = any(k in " ".join(alts).lower() for k in drawn)
        if not alt_kind:
            fails.append(f"kind: drawn {sorted(drawn) or 'nothing'}, want {kind}")
    best = None
    for scale in _scale_from_alts(alts):
        ff = []
        if kind in ("bar", "hbar"):
            check_bar(e, f, ff, notes, scale)
        elif kind in ("grouped_bar", "stacked_bar"):
            check_grouped(e, f, ff, notes, kind == "stacked_bar", scale)
        elif kind == "pie":
            check_pie(e, f, ff, notes, scale)
        else:
            break
        if best is None or len(ff) < len(best):
            best = ff
        if not ff:
            break
    if best is not None:
        fails += best
    elif kind == "line":
        check_line(e, f, fails, notes)
    elif kind == "scatter":
        check_scatter(e, f, fails, notes, alts)
    elif kind == "histogram":
        check_hist(e, f, fails, notes)
    elif kind == "heatmap":
        check_heatmap(e, f, fails, notes)
    check_asks(e.get("asks"), f, None, fails, unchecked, notes)
    return fails, unchecked, notes


def check(expect, facts, result, spec=None, item=None, turn=None):
    e = expect or {}
    out = {"kind_expected": e.get("kind"), "failed": [], "unchecked": [], "n_checks": 0, "n_failed": 0}
    if not (result or {}).get("ok"):
        out.update({"pass": False, "failed": [f"run: no plot ({str((result or {}).get('error', ''))[:150]})"], "n_checks": 1, "n_failed": 1})
        return out
    if not facts:
        out.update({"pass": False, "failed": ["run: no figure facts"], "n_checks": 1, "n_failed": 1})
        return out
    best = None
    for i, f in enumerate(facts):
        fails, unchecked, notes = check_figure(e, f)
        if best is None or len(fails) < len(best[1]):
            best = (i, fails, unchecked, notes)
    i, fails, unchecked, notes = best
    n_checks = 2 + len(e.get("asks") or [])
    out.update({"pass": not fails, "failed": fails, "unchecked": unchecked, "notes": notes, "figure": i,
                "n_checks": n_checks, "n_failed": len(fails)})
    return out
