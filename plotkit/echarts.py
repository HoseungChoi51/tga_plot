"""
plotkit.echarts - the ECharts engine for plotkit's curves.

plotkit.core keeps reading the files, choosing the columns and computing the residue and
peaks. This module turns that into an engine-neutral "resolved plot" (numbers, colours,
texts and tick positions, nothing matplotlib-specific) and hands it to Node
(plotkit/js/render.mjs), which draws it with ECharts and writes SVG, PNG or PDF.

Use:  PLOTKIT_ENGINE=echarts python -m plotkit plot spec.json     (or --engine echarts)
      python -c "import plotkit; print(plotkit.plot({...}, engine='echarts'))"

The model never writes code for this engine. Anything no key covers goes in the
"echarts" key: a partial ECharts option, checked here against an allowlist (validate_patch).
"""
import copy
import difflib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

from . import core as pk
from .core import PlotkitError

HERE = Path(__file__).parent
NODE_DIR = HERE / "js"
PT = 96 / 72                 # points -> CSS pixels (the SVG is laid out at 96 px per inch)
SMALL = 0.833                # matplotlib's "small" font size factor
PATCH_MAX_BYTES = 4096

# =================================================================== allowlist for "echarts"
_STYLE = {"color": None, "fontSize": None, "fontWeight": None, "fontFamily": None, "fontStyle": None,
          "lineHeight": None}
_LINE = {"color": None, "width": None, "type": None, "opacity": None, "dashOffset": None}
_ITEM = {"color": None, "opacity": None, "borderColor": None, "borderWidth": None, "borderType": None}
_LABEL = {"show": None, "position": None, "color": None, "fontSize": None, "fontWeight": None,
          "formatter": None, "distance": None, "offset": None, "rotate": None, "align": None,
          "verticalAlign": None, "backgroundColor": None, "padding": None, "borderRadius": None,
          "borderColor": None, "borderWidth": None}
_MARK_ITEM = {"name": None, "xAxis": None, "yAxis": None, "coord": None, "value": None, "type": None,
              "symbol": None, "symbolSize": None, "symbolRotate": None, "label": _LABEL,
              "lineStyle": _LINE, "itemStyle": _ITEM}
_MARK = {"silent": None, "symbol": None, "symbolSize": None, "precision": None, "label": _LABEL,
         "lineStyle": _LINE, "itemStyle": _ITEM, "data": "MARKDATA"}
_AXIS = {"name": None, "nameLocation": None, "nameGap": None, "nameRotate": None, "nameTextStyle": _STYLE,
         "min": None, "max": None, "interval": None, "inverse": None, "type": None, "logBase": None,
         "splitNumber": None, "minInterval": None, "maxInterval": None, "show": None, "position": None,
         "offset": None,
         "axisLine": {"show": None, "onZero": None, "lineStyle": _LINE},
         "axisTick": {"show": None, "inside": None, "length": None, "interval": None, "lineStyle": _LINE,
                      "customValues": None},
         "axisLabel": {"show": None, "inside": None, "color": None, "fontSize": None, "fontWeight": None,
                       "rotate": None, "margin": None, "formatter": None, "customValues": None,
                       "showMinLabel": None, "showMaxLabel": None},
         "splitLine": {"show": None, "lineStyle": _LINE},
         "minorTick": {"show": None, "splitNumber": None, "length": None, "lineStyle": _LINE},
         "minorSplitLine": {"show": None, "lineStyle": _LINE},
         "splitArea": {"show": None}}
_SERIES = {"name": None, "lineStyle": _LINE, "itemStyle": _ITEM,
           "areaStyle": {"color": None, "opacity": None, "origin": None},
           "symbol": None, "symbolSize": None, "showSymbol": None, "smooth": None, "step": None, "z": None,
           "label": _LABEL, "emphasis": {"disabled": None},
           "markArea": _MARK, "markLine": _MARK, "markPoint": _MARK}
_GRAPHIC = {"type": None, "id": None, "left": None, "right": None, "top": None, "bottom": None,
            "x": None, "y": None, "z": None, "rotation": None, "silent": None,
            "style": {"text": None, "fill": None, "stroke": None, "lineWidth": None, "lineDash": None,
                      "fontSize": None, "font": None, "fontWeight": None, "fontFamily": None, "opacity": None,
                      "textAlign": None, "textVerticalAlign": None, "align": None, "verticalAlign": None,
                      "backgroundColor": None, "padding": None},
            "shape": {"x": None, "y": None, "width": None, "height": None, "r": None,
                      "x1": None, "y1": None, "x2": None, "y2": None}}
ALLOWED = {"title": {"show": None, "text": None, "subtext": None, "left": None, "right": None, "top": None,
                     "bottom": None, "textAlign": None, "textStyle": _STYLE, "subtextStyle": _STYLE},
           "legend": {"show": None, "left": None, "right": None, "top": None, "bottom": None, "orient": None,
                      "itemGap": None, "itemWidth": None, "itemHeight": None, "icon": None, "padding": None,
                      "backgroundColor": None, "borderColor": None, "borderWidth": None, "textStyle": _STYLE},
           "grid": {"show": None, "left": None, "right": None, "top": None, "bottom": None,
                    "borderColor": None, "borderWidth": None, "backgroundColor": None},
           "xAxis": _AXIS, "yAxis": [_AXIS], "series": [_SERIES], "graphic": [_GRAPHIC],
           "backgroundColor": None, "textStyle": _STYLE}
GRAPHIC_TYPES = ("text", "line", "rect")
PATCH_ALIASES = {"colour": "color", "dash": "type", "linestyle": "type", "line_style": "type", "style": "type",
                 "fontsize": "fontSize", "font_size": "fontSize", "size": "fontSize", "linewidth": "width",
                 "line_width": "width", "lw": "width", "alpha": "opacity", "label_text": "formatter",
                 "text": "formatter", "x_axis": "xAxis", "xaxis": "xAxis", "y_axis": "yAxis", "yaxis": "yAxis",
                 "markline": "markLine", "markarea": "markArea", "markpoint": "markPoint",
                 "linestyles": "lineStyle", "line": "lineStyle", "textstyle": "textStyle"}
_BAD_STRING = re.compile(r"^\s*(https?:|data:|file:|javascript:|ftp:)|function\s*\(|=>", re.I)


def _patch_error(path, key, allowed):
    keys = [k for k in allowed]
    alias = PATCH_ALIASES.get(key.lower().replace(" ", ""))
    guess = alias if alias in keys else (difflib.get_close_matches(key, keys, n=1, cutoff=0.5) or [None])[0]
    where = f"{path}.{key}" if path else key
    hint = f"did you mean {path + '.' if path else ''}{guess}?" if guess else ""
    raise PlotkitError(f'unknown path "echarts.{where}"',
                       (hint + " " if hint else "") + f"allowed here: {', '.join(keys)}")


def _check_value(v, path):
    if isinstance(v, str):
        if _BAD_STRING.search(v):
            raise PlotkitError(f"echarts.{path}: links, data URLs and code are not allowed",
                               "write plain text, numbers or colours only")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _check_value(x, f"{path}[{i}]")
    elif isinstance(v, dict):
        raise PlotkitError(f"echarts.{path} must be a plain value, not an object")
    elif not (v is None or isinstance(v, (bool, int, float))):
        raise PlotkitError(f"echarts.{path}: unsupported value {v!r}")


def _check_mark_data(v, path):
    """markArea/markLine/markPoint data: a list of items, or of [start, end] pairs of items."""
    if not isinstance(v, list):
        raise PlotkitError(f"echarts.{path} must be a list", 'e.g. "data": [[{"xAxis": 300}, {"xAxis": 450}]]')
    if len(v) > 50:
        raise PlotkitError(f"echarts.{path} has more than 50 items", "annotations only; the data comes from the file")
    for i, item in enumerate(v):
        pair = item if isinstance(item, list) else [item]
        if len(pair) > 2:
            raise PlotkitError(f"echarts.{path}[{i}] must be one item or a [start, end] pair")
        for j, it in enumerate(pair):
            p = f"{path}[{i}]" + (f"[{j}]" if isinstance(item, list) else "")
            if not isinstance(it, dict):
                raise PlotkitError(f"echarts.{p} must be an object like {{\"xAxis\": 300}}")
            _check(it, _MARK_ITEM, p)


def _check(v, allowed, path):
    if allowed == "MARKDATA":
        return _check_mark_data(v, path)
    if isinstance(allowed, list):            # a list of objects (yAxis, series, graphic)
        items = v if isinstance(v, list) else [v]
        if path == "yAxis" and len(items) > 2:
            raise PlotkitError("echarts.yAxis has more than 2 entries", "0 = y1 (left), 1 = y2 (right)")
        for i, it in enumerate(items):
            if it is None or it == {}:
                continue                     # a placeholder to reach a later index
            if not isinstance(it, dict):
                raise PlotkitError(f"echarts.{path}[{i}] must be an object (or {{}} to skip it)")
            _check(it, allowed[0], f"{path}[{i}]")
            if path == "graphic" and it.get("type") not in GRAPHIC_TYPES:
                raise PlotkitError(f"echarts.graphic[{i}].type must be one of {', '.join(GRAPHIC_TYPES)}")
        return
    if isinstance(allowed, dict):
        if not isinstance(v, dict):
            raise PlotkitError(f"echarts.{path} must be an object")
        for k, x in v.items():
            if k not in allowed:
                _patch_error(path, k, allowed)
            _check(x, allowed[k], f"{path}.{k}" if path else k)
        return
    _check_value(v, path)


def validate_patch(patch):
    """Check an "echarts" value against the allowlist. Returns a clean copy or raises PlotkitError."""
    if isinstance(patch, str):
        try:
            patch = json.loads(patch)
        except json.JSONDecodeError:
            raise PlotkitError('"echarts" must be an object (a partial ECharts option)',
                               'e.g. "echarts": {"series": [{"lineStyle": {"type": "dotted"}}]}')
    if not isinstance(patch, dict):
        raise PlotkitError('"echarts" must be an object (a partial ECharts option)',
                           'e.g. "echarts": {"series": [{"lineStyle": {"type": "dotted"}}]}')
    if len(json.dumps(patch, ensure_ascii=False).encode()) > PATCH_MAX_BYTES:
        raise PlotkitError(f'"echarts" is larger than {PATCH_MAX_BYTES} bytes', "keep it to the few settings no key covers")
    fixed = {}
    for k, v in patch.items():               # "xaxis" -> "xAxis" etc. at the top level only
        k2 = k if k in ALLOWED else PATCH_ALIASES.get(k.lower(), k)
        fixed[k2] = v
    _check(fixed, ALLOWED, "")
    for k in ("yAxis", "series", "graphic"):
        if k in fixed and not isinstance(fixed[k], list):
            fixed[k] = [fixed[k]]
    return copy.deepcopy(fixed)


# =================================================================== resolving
def _hex(c):
    from .colors import to_hex
    return to_hex(c)


def _rgba(c, alpha):
    from .colors import to_rgb
    r, g, b = (round(255 * v) for v in to_rgb(c))
    return f"rgba({r},{g},{b},{alpha:g})"


def _clean(v):
    v = float(v)
    return float(f"{v:.10g}")


def _ticks(lo, hi, axspec):
    """Tick values inside [lo, hi], the same ones matplotlib would pick."""
    from .ticks import tick_values
    if axspec.get("log"):
        return None
    step = axspec.get("step")
    if step:
        off = (axspec["min"] % step) if axspec.get("min") is not None else 0.0
        k0 = np.ceil((lo - off) / step - 1e-9)
        vals = off + step * np.arange(k0, np.floor((hi - off) / step + 1e-9) + 1)
    else:
        vals = tick_values(lo, hi, "auto")
        vals = vals[(vals >= lo - 1e-9 * abs(hi - lo)) & (vals <= hi + 1e-9 * abs(hi - lo))]
        if len(vals) > 9:              # matplotlib's auto nbins thins for a ~4.5 in plot
            vals = tick_values(lo, hi, 7)
            vals = vals[(vals >= lo) & (vals <= hi)]
    return [_clean(v) for v in vals]


def _axis_range(axspec, data_min, data_max, pad_lo, pad_hi, tight=False):
    """The same limits as plotkit._apply_axis, plus the tick values."""
    lo, hi = axspec.get("min"), axspec.get("max")
    rng = (data_max - data_min) or 1.0
    if lo is None:
        lo = data_min if tight else data_min - pad_lo * rng
    if hi is None:
        hi = data_max if tight else data_max + pad_hi * rng
    if hi <= lo:
        raise PlotkitError(f"axis range is empty (min {lo} >= max {hi})")
    step = axspec.get("step")
    if step and not axspec.get("log") and (hi - lo) / step > 60:
        raise PlotkitError(f"step {step} is too small for range {lo:g}..{hi:g}", "use a larger step")
    return _clean(lo), _clean(hi), _ticks(lo, hi, axspec)


def _font_family(spec, texts):
    if spec["font"]:
        return f"{spec['font']}, sans-serif", None
    korean = any(re.search(r"[가-힣ㄱ-ㆎ]", t or "") for t in texts)
    if korean:
        return ("Malgun Gothic, Apple SD Gothic Neo, AppleGothic, NanumGothic, Noto Sans CJK KR, "
                "Noto Sans KR, WenQuanYi Zen Hei, sans-serif"), None
    return "DejaVu Sans, Arial, Helvetica, sans-serif", None


def _annotations(spec, axes_on, j, colors, results, stack, combine_color, text_all):
    """Same choices as plotkit._annotate, but returned as data instead of drawn."""
    out = []
    tc = spec["text_color"]
    base = spec["font_size"]
    yoff = j.get("yoff", 0.0)
    for name, a in list(spec["annotate"].items()) + list(j.get("marks", {}).items()):
        t = a["type"]
        on = a.get("on", "y1")
        sheet = j["sheet"]
        if t in ("value_at_x", "peak", "hline") and on not in axes_on:
            results.append({"name": name, "sheet": sheet, "skipped": f"{on} is not drawn"})
            continue
        ax = on if on in axes_on else "y1"
        col = a.get("color") or combine_color or colors.get(on, tc)
        tcol = tc if text_all and not a.get("color") else col
        fs = a.get("size") or base * SMALL
        data = j["data"]
        if t == "value_at_x":
            X, Y = data["x"], data[on]
            xu, yv = pk.value_at_x(X, Y, a["x"], a.get("method", "nearest"))
            if xu is None:
                results.append({"name": name, "sheet": sheet, "x": a["x"], "value": None,
                                "note": f"x={a['x']:g} is outside the data ({np.nanmin(X):.0f}..{np.nanmax(X):.0f})"})
                if a.get("_requested"):
                    out.append({"kind": "note", "name": name, "axis": ax, "stack": stack,
                                "text": f"{name}: no data at x = {a['x']:g}\n(data ends at {np.nanmax(X):.0f})",
                                "color": _hex(tc if text_all else (combine_color or "gray")), "size": base * SMALL})
                continue
            text = a.get("text", "{y:.1f}")
            unit = pk._unit(j["cols"][on]["name"]) if on in j["cols"] else None
            if a.get("_preset_text") and unit and not pk._same_unit(unit, "%"):
                text = text.replace("{y:.1f}%", "{y:.3g} " + unit)
            shown = yv - (yoff if on == "y1" else 0.0)          # offset curves keep their real values
            label = pk._fmt(text, xu, shown, "y")
            out.append({"kind": "value", "name": name, "axis": ax, "x": _clean(xu), "y": _clean(yv), "text": label,
                        "color": _hex(col), "text_color": _hex(tcol), "size": fs, "stack": stack})
            results.append({"name": name, "sheet": sheet, "x_requested": a["x"], "x_used": round(xu, 3),
                            "value": round(shown, 4), "text": label})
        elif t == "peak":
            kind = a.get("kind", "max")
            peaks = pk.find_peaks_xy(data["x"], data[on], a.get("count", 1), kind,
                                     a.get("x_min"), a.get("x_max"), a.get("min_rel", 0.1))
            for xp, yp in peaks:
                out.append({"kind": "peak", "name": name, "axis": ax, "x": _clean(xp), "y": _clean(yp),
                            "text": pk._fmt(a.get("text", "{x:.0f}"), xp, yp, "x"), "color": _hex(col),
                            "text_color": _hex(tcol), "size": fs, "down": kind != "max"})
            results.append({"name": name, "sheet": sheet, "peaks": [
                {"x": round(xp, 3), "y": round(yp, 5), "text": pk._fmt(a.get("text", "{x:.0f}"), xp, yp, "x")}
                for xp, yp in peaks]})
        elif t in ("vline", "hline"):
            pos = a["x"] if t == "vline" else a["y"]
            if stack == 0:
                txt = a.get("text")
                out.append({"kind": t, "name": name, "axis": ax, "value": _clean(pos),
                            "color": _hex(a.get("color") or "gray"),
                            "linestyle": a.get("linestyle", "dashed"),
                            "text": pk._fmt(txt, pos, None, "x") if (txt and t == "vline")
                            else (pk._fmt(txt, None, pos, "y") if txt else ""),
                            "text_color": _hex(a.get("color") or (tc if text_all else "gray")), "size": fs})
            results.append({"name": name, "sheet": sheet, ("x" if t == "vline" else "y"): pos})
        elif t == "band":
            if stack == 0:
                c = a.get("color") or "gray"
                out.append({"kind": "band", "name": name, "x_min": _clean(a["x_min"]), "x_max": _clean(a["x_max"]),
                            "fill": _rgba(c, a.get("alpha", 0.15)), "text": a.get("text") or "",
                            "text_color": _hex(a.get("color") or (tc if text_all else "gray")), "size": fs})
            results.append({"name": name, "sheet": sheet, "x_min": a["x_min"], "x_max": a["x_max"]})
        elif t == "text" and a.get("x") is not None and a.get("y") is not None:
            out.append({"kind": "text_at", "name": name, "axis": ax, "x": _clean(a["x"]), "y": _clean(a["y"]),
                        "text": a.get("text", ""), "color": _hex(a.get("color") or tc), "size": fs})
            results.append({"name": name, "sheet": sheet, "text": a.get("text", ""), "x": a["x"], "y": a["y"]})
        elif t == "text":
            if stack == 0:
                out.append({"kind": "text", "name": name, "where": a.get("where", "upper right"),
                            "text": a.get("text", ""), "color": _hex(a.get("color") or tc), "size": fs})
            results.append({"name": name, "sheet": sheet, "text": a.get("text", "")})
    return out


def resolve(spec, jobs):
    """Normalized spec + jobs -> list of (group, figure dict, annotation results)."""
    tc = spec["text_color"]
    text_all = spec["_text_color_set"]
    groups = [jobs] if spec["combine"] else [[j] for j in jobs]
    figs = []
    for group in groups:
        first = group[0]
        title = pk.figure_title(spec, first)
        texts = [title] + [spec[r].get("label") or "" for r in ("x", "y1", "y2")] + \
                [j["sheet"] for j in group] + [c["name"] for j in group for c in j["cols"].values()] + \
                [a.get("text") or "" for a in spec["annotate"].values()] + \
                [json.dumps(spec["echarts"] or {}, ensure_ascii=False)] + [str(n) for n in spec.get("names") or []] + \
                [str(a.get("text") or "") for j in group for a in j.get("marks", {}).values()]
        family, _ = _font_family(spec, texts)
        has_y2 = all("y2" in j["data"] for j in group)
        n = len(group)
        series, legend_names, legend_extra = [], [], []
        split = bool(spec.get("panels")) and all("y2" in j["data"] for j in group)
        for k, j in enumerate(group):
            c1, c2, lab1 = pk.series_style(spec, j, k)
            j["colors"] = {"y1": c1, "y2": c2}
            series.append({"axis": "y1", "name": lab1, "sheet": j["sheet"], "color": _hex(c1),
                           "width": spec["y1"].get("width", 1.5), "linestyle": spec["y1"].get("linestyle", "solid"),
                           "style": spec["y1"].get("style", "line"),
                           "points": [[_clean(a), _clean(b)] for a, b in zip(j["data"]["x"], j["data"]["y1"])]})
            legend_names.append(lab1)
        if has_y2:
            for k, j in enumerate(group):
                lab2 = None if spec["combine"] else (spec["y2"].get("legend") or pk._labels(spec, "y2", j["cols"]["y2"]))
                series.append({"axis": "y2", "name": lab2 or f"{j['sheet']} (y2)", "sheet": j["sheet"],
                               "color": _hex(j["colors"]["y2"]), "width": spec["y2"].get("width", 1.5),
                               "linestyle": "dashed" if spec["combine"] and not split else spec["y2"].get("linestyle", "solid"),
                               "style": spec["y2"].get("style", "line"),
                               "points": [[_clean(a), _clean(b)] for a, b in zip(j["data"]["x"], j["data"]["y2"])]})
                if lab2:
                    legend_names.append(lab2)
        if spec["combine"] and has_y2 and not split:
            legend_extra = [{"name": pk._labels(spec, "y1", first["cols"]["y1"]), "color": "#808080", "linestyle": "solid"},
                            {"name": pk._labels(spec, "y2", first["cols"]["y2"]), "color": "#808080", "linestyle": "dashed"}]

        def axis(role, values, pads, tight=False):
            a = spec[role]
            line_c = None if (spec["combine"] or role == "x") else a.get("color")
            text_c = tc if text_all else (line_c or tc)
            lo, hi, ticks = _axis_range(a, float(np.nanmin(values)), float(np.nanmax(values)), *pads, tight=tight)
            return {"label": pk._labels(spec, role, first["cols"][role]),
                    "label_size": a.get("label_size") or spec["font_size"],
                    "label_color": _hex(a.get("label_color") or text_c),
                    "tick_size": a.get("tick_size") or spec["font_size"],
                    "tick_color": _hex(a.get("tick_color") or text_c),
                    "tick_mark_color": _hex(a.get("tick_color") or line_c or tc),
                    "line_color": _hex(line_c) if line_c else None,
                    "min": lo, "max": hi, "ticks": ticks, "log": bool(a.get("log")),
                    "inverse": bool(a.get("invert")), "minor": bool(a.get("minor"))}
        axes = {"x": axis("x", np.concatenate([j["data"]["x"] for j in group]), (0, 0), tight=True),
                "y1": axis("y1", np.concatenate([j["data"]["y1"] for j in group]), (0.08, 0.12))}
        axes["y2"] = axis("y2", np.concatenate([j["data"]["y2"] for j in group]), (0.12, 0.18)) if has_y2 else None
        if not has_y2:
            axes["y1"]["line_color"] = None       # a single y axis keeps a black frame, as in matplotlib

        ann_results, anns = [], []
        axes_on = ["y1"] + (["y2"] if has_y2 else [])
        for k, j in enumerate(group):
            anns += _annotations(spec, axes_on, j, j["colors"], ann_results, k,
                                 j["colors"]["y1"] if spec["combine"] else None, text_all)
        lg = spec["legend"]
        figs.append((group, {
            "size_in": [float(v) for v in spec["size"]], "dpi": float(spec["dpi"]),
            "font_family": family, "font_size": float(spec["font_size"]), "text_color": _hex(tc),
            "title": {"text": title, "size": spec["title"].get("size") or spec["font_size"] * 1.2,
                      "color": _hex(spec["title"].get("color") or tc)},
            "tick_direction": spec["tick_direction"], "grid": bool(spec["grid"]),
            "axes": axes, "series": series,
            "series_index": "y1 per sheet, then y2 per sheet" if spec["combine"] else "0 = y1, 1 = y2",
            "legend": {"show": bool(lg["show"]), "where": lg["where"], "size": lg["size"] or spec["font_size"] * SMALL,
                       "names": legend_names, "extra": legend_extra, "color": _hex(tc)},
            "annotations": anns, "box_peaks": bool(spec["combine"]), "panels": "split" if split else None,
            "echarts": spec["echarts"],
        }, ann_results))
    return figs


# =================================================================== Node bridge
def _node():
    exe = os.environ.get("PLOTKIT_NODE") or shutil.which("node")
    if not exe:
        raise PlotkitError("the ECharts engine needs Node.js 20 or newer, and node was not found",
                           "install Node.js, or set PLOTKIT_NODE to node's full path, or use the matplotlib engine")
    if not (NODE_DIR / "node_modules" / "echarts").exists():
        raise PlotkitError("the ECharts engine's Node packages are not installed", f"run: npm install --prefix \"{NODE_DIR}\"")
    return exe


def render(figures, timeout=180):
    """Send resolved figures to plotkit/js/render.mjs. Returns its JSON reply."""
    payload = json.dumps({"figures": figures}, ensure_ascii=False)
    env = dict(os.environ)
    try:
        p = subprocess.run([_node(), str(NODE_DIR / "render.mjs")], input=payload.encode("utf-8"),
                           capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise PlotkitError(f"the ECharts renderer took longer than {timeout} s", "try fewer sheets or formats")
    out = p.stdout.decode("utf-8", "replace").strip()
    try:
        reply = json.loads(out.splitlines()[-1]) if out else None
    except json.JSONDecodeError:
        reply = None
    if not reply:
        err = p.stderr.decode("utf-8", "replace").strip().splitlines()
        raise PlotkitError("the ECharts renderer failed: " + (err[-1] if err else f"exit code {p.returncode}"),
                           f"run: npm install --prefix \"{NODE_DIR}\"; for PDF also set PLOTKIT_CHROMIUM or run npx playwright install chromium")
    if not reply.get("ok"):
        raise PlotkitError(reply.get("error", "the ECharts renderer failed"), reply.get("hint", ""))
    return reply


def live_result(user_spec):
    """ECharts options for a live chart in the browser (labels tied to the data, zoom, tooltip), one per figure, in
    the shared result shape (see plotkit.core.plot) with "options" and nothing saved. Node builds them (js/live.mjs)."""
    spec = pk.normalize_spec(user_spec)
    if spec["code"]:
        raise PlotkitError('"code" (Python) does not work with the ECharts engine',
                           'use a key (e.g. annotate band for shading), or put ECharts settings in "echarts"')
    jobs, warnings = pk.build_jobs(spec)
    figs = resolve(spec, jobs)
    try:
        p = subprocess.run([_node(), str(NODE_DIR / "live.mjs")],
                           input=json.dumps({"figures": [f for _, f, _ in figs]}, ensure_ascii=False).encode("utf-8"),
                           capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise PlotkitError("the live ECharts option took longer than 60 s", "try fewer sheets")
    out = p.stdout.decode("utf-8", "replace").strip()
    try:
        reply = json.loads(out.splitlines()[-1]) if out else None
    except json.JSONDecodeError:
        reply = None
    if reply and not reply.get("ok") and reply.get("hint") is not None:     # the spec's "echarts" patch, as render() says
        raise PlotkitError(reply.get("error", "live option failed"), reply["hint"])
    if not reply or not reply.get("ok"):
        err = (reply or {}).get("error") or (p.stderr.decode("utf-8", "replace").strip().splitlines() or ["?"])[-1]
        raise PlotkitError("live option failed: " + err, f'check Node and run: npm install --prefix "{NODE_DIR}"')
    return {"ok": True, "kind": "curve", "engine": "echarts", "options": reply["options"], "saved": [],
            "warnings": warnings, "not_done": pk.not_done(spec),
            "values": pk.curve_values([{"annotations": ann} for _, _, ann in figs])}


def live_options(user_spec):
    """The curve's live ECharts options, one per figure (see live_result)."""
    return live_result(user_spec)["options"]


def plot_echarts(user_spec, out_dir=None, formats=None, summary_csv=True):
    """Draw a curve spec with ECharts (see plotkit.core.plot)."""
    spec = pk.set_output(pk.normalize_spec(user_spec), out_dir, formats)
    if spec["code"]:
        raise PlotkitError('"code" (Python) does not work with the ECharts engine',
                           'use a key (e.g. annotate band for shading), or put ECharts settings in "echarts"')
    jobs, warnings = pk.build_jobs(spec)
    outdir, name_tpl = pk.output_target(spec)
    figs = resolve(spec, jobs)
    payload = []
    for group, fig, _ in figs:
        stem = pk.file_stem(name_tpl, spec, group[0])
        fig["outputs"] = [{"format": f, "path": str(outdir / f"{stem}.{f}")} for f in spec["output"]["format"]]
        fig["n_series"] = len(fig["series"])
        payload.append(fig)
    reply = render(payload)
    results = []
    for (group, fig, ann), done in zip(figs, reply["figures"]):
        first = group[0]
        for w in done.get("warnings", []):
            if w not in warnings:
                warnings.append(w)
        results.append({
            "sheet": "all" if spec["combine"] else first["sheet"],
            "file": Path(first["file"]).name,
            "saved": done["saved"],
            "rows_plotted": sum(j["rows"] for j in group),
            "columns_used": {j["sheet"]: {r: f'{c["letter"]} "{c["name"]}"' for r, c in j["cols"].items()}
                             for j in group},
            "column_guess": first["how"] or "as given",
            "annotations": ann,
        })
    if summary_csv:
        pk._write_summary(outdir, results)
    return pk.curve_result("echarts", outdir, results, warnings, spec)
