#!/usr/bin/env python3
"""
plotkit.core - spec-driven plots of lab data (TGA preset built in): the file reader, the curve spec
(normalize, error + hint), the matplotlib engine and the router that sends chart specs to plotkit.charts.

COMMAND LINE
  1. Look at the data first:   python -m plotkit inspect FILE
  2. Write a JSON spec with ONLY what the user asked for (everything else has defaults).
  3. Plot:                     python -m plotkit plot SPEC.json
                               (or: python -m plotkit plot --json '{"file": "TGA.xlsx"}')
  4. Read the JSON that is printed. If "ok" is false, fix the spec using "hint" and retry.
  Engines: ECharts (default; needs Node, see plotkit/js/README.md) or matplotlib (optional:
                               pip install "plotkit[matplotlib]"; --engine matplotlib or PLOTKIT_ENGINE=matplotlib)
  Every change the user can ask for is a spec key:
                               python -m plotkit schema     (all keys)
                               python -m plotkit example    (a full example spec)

Smallest useful spec (TGA preset: Temperature on x, Weight % on the left axis,
Deriv. weight on the right axis, residue at 800 °C and DTG peak labelled):
  {"file": "TGA.xlsx"}

Reads .xlsx/.xlsm/.xls and text files (.csv/.txt/.tsv/.dat/anything else) with
blank or metadata rows on top, units rows, extra columns, Korean headers,
tab/comma/semicolon/space separators and decimal commas.

Python use:  from plotkit import plot, inspect_file;  plot({"file": "TGA.xlsx"})
Requires:    numpy, pandas, scipy, openpyxl (+ xlrd for old .xls files; + matplotlib for the matplotlib engine)
"""
import copy
import difflib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

__version__ = "2.0"


class PlotkitError(Exception):
    def __init__(self, message, hint=""):
        super().__init__(message)
        self.message = message
        self.hint = hint


# =================================================================== spec
TGA_PRESET = {
    "x": {"label": "Temperature (°C)"},
    "y1": {"label": "Weight (%)", "color": "#1f4e9c"},
    "y2": {"label": "Deriv. weight (%/°C)", "color": "#c0392b", "flip": "peaks_up"},
    "annotate": {
        "residue": {"type": "value_at_x", "on": "y1", "x": 800, "method": "nearest",
                    "text": "Residue {y:.1f}%"},
        "peak": {"type": "peak", "on": "y2", "count": 1, "x_min": 150,
                 "text": "{x:.0f} °C"},
    },
}

DEFAULTS = {
    "file": None,
    "sheets": "all",
    "preset": "tga",
    "read": {"header_row": None, "data_start_row": None, "sep": None,
             "decimal": None, "encoding": None},
    "x": {"col": None, "label": None, "min": None, "max": None, "step": None, "log": False,
          "label_size": None, "label_color": None, "tick_size": None, "tick_color": None,
          "minor": False, "invert": False},
    "y1": {"col": None, "label": None, "min": None, "max": None, "step": None,
           "color": "#1f4e9c", "width": 1.8, "linestyle": "solid", "style": "line",
           "flip": "none", "log": False, "legend": None, "show": True,
           "label_size": None, "label_color": None, "tick_size": None, "tick_color": None,
           "minor": False, "invert": False},
    "y2": {"col": None, "label": None, "min": None, "max": None, "step": None,
           "color": "#c0392b", "width": 1.4, "linestyle": "solid", "style": "line",
           "flip": "none", "log": False, "legend": None, "show": True,
           "label_size": None, "label_color": None, "tick_size": None, "tick_color": None,
           "minor": False, "invert": False},
    "annotate": {},
    "title": {"text": "{sheet}", "size": None, "color": None},
    "legend": {"where": "center left", "show": True, "size": None},
    "text_color": "black",
    "tick_direction": "in",
    "code": None,
    "echarts": None,
    "grid": False,
    "size": [6.4, 4.6],
    "dpi": 300,
    "font": None,
    "font_size": 11,
    "combine": False,
    "colors": None,
    "names": None,
    "offset": None,
    "panels": None,
    "data_code": None,
    "asks": [],
    "output": {"dir": None, "format": "png", "name": None},
}

ANNOT_KEYS = {"type", "on", "x", "y", "method", "text", "color", "size", "count", "kind",
              "x_min", "x_max", "min_rel", "where", "marker", "linestyle", "alpha"}
ANNOT_TYPES = {"value_at_x", "peak", "vline", "hline", "text", "band"}
ENGINES = ("matplotlib", "echarts")

SCHEMA_DOC = {
    "file": "data file path, or a list of paths (xlsx/xls/csv/txt/...)",
    "sheets": '"all" (default), a sheet name, a 1-based sheet number, or a list of those',
    "preset": '"tga" (default; TGA labels, residue + DTG peak) or "none" (plain plot, you must give x.col and y1.col)',
    "read.header_row": "1-based row of the column names; normally automatic",
    "read.data_start_row": "1-based first row of numbers; normally automatic",
    "read.sep": 'text files only: "," ";" "\\t" "space"; normally automatic',
    "read.decimal": 'text files only: "." or ","; normally automatic',
    "read.encoding": 'text files only, e.g. "utf-8", "cp949", "utf-16"; normally automatic',
    "x|y1|y2.col": 'column letter like "B" (as in Excel; for text files A = 1st field) or part of the column name like "Temperature"',
    "x|y1|y2.label": "axis label text (default: the preset's label, or the column's name when its unit differs, e.g. Weight (mg))",
    "x|y1|y2.min / max": "axis range; leave out for automatic",
    "x|y1|y2.step": "distance between tick marks, e.g. 200 or 0.2",
    "x|y1|y2.log": "true for a log axis",
    "x|y1|y2.label_size / label_color": "font size / color of the axis label (y labels default to the line color)",
    "x|y1|y2.tick_size / tick_color": "font size / color of the tick numbers (y ticks default to the line color)",
    "y1|y2.color": 'line color: name ("red", "빨강"), or hex "#c0392b"',
    "y1|y2.width": "line width (default 1.8 / 1.4)",
    "y1|y2.linestyle": '"solid" | "dashed" | "dotted" | "dashdot"',
    "y1|y2.style": '"line" | "scatter" | "line+marker"',
    "y1|y2.flip": '"none" | "flip" (multiply by -1) | "peaks_up" | "peaks_down"',
    "y1|y2.legend": "name in the legend (default: the axis label)",
    "y2": "false to draw no second axis",
    "annotate.<name>": 'dict of labels; set one to false to remove a preset label (e.g. "peak": false), '
                       'true to ask for a preset label as it is (e.g. "residue": true). A value_at_x label with '
                       'no data at its x shows "no data" only when the spec names it; otherwise it is left out',
    "annotate.<name>.type": '"value_at_x" | "peak" | "vline" | "hline" | "text" | "band" (guessed from the name: residue*/value* -> value_at_x, peak*/max* -> peak, band*/shade* -> band)',
    "annotate.<name>.on": '"y1" or "y2"',
    "annotate.<name>.x": "value_at_x / vline: the x position, e.g. 800",
    "annotate.<name>.y": "hline: the y position",
    "annotate.<name>.method": 'value_at_x: "nearest" (closest measured point, default) or "interp"',
    "annotate.<name>.count": "peak: how many peaks to label (default 1)",
    "annotate.<name>.kind": 'peak: "max" (default) or "min"',
    "annotate.<name>.x_min / x_max": "peak: only search in this x range; band: the shaded x range (both needed)",
    "annotate.<name>.alpha": "band: opacity of the shading, 0..1 (default 0.15)",
    "annotate.<name>.min_rel": "peak: extra peaks must be at least this fraction of the main one (default 0.1)",
    "annotate.<name>.text": 'label template: {x} {y} or {} (e.g. "Residue {}%", "{x:.0f} °C", "Residue {y:.2f}%"); '
                            "the preset residue label uses the column's unit when it isn't %, e.g. \"Residue 0.82 mg\"",
    "annotate.<name>.where": 'text: "upper left" | "upper right" | "lower left" | "lower right"',
    "annotate.<name>.color": "label color (default: the line color)",
    "annotate.<name>.size": "label font size",
    "title": 'plot title text, or {"text": ..., "size": ..., "color": ...}; "{sheet}" (default) and "{file}" are replaced; "" for none',
    "legend": 'legend position "center left" (default), "best", "upper right", "lower left", ..., "none"; or {"where": ..., "show": true/false, "size": ...}',
    "text_color": "color of all text that has no color of its own (default black); when given, also the y-axis "
                  "labels, tick labels and residue/peak labels, which otherwise follow the line colors",
    "tick_direction": '"in" (default), "out" or "inout"',
    "code": "matplotlib engine only: extra Python run after drawing, before saving. Names: fig, ax1 (left y), ax2 (right y or None), x, y1, y2 (arrays), sheet, plt, np. Use only for things no key covers.",
    "echarts": "ECharts engine only: a partial ECharts option merged over the drawn plot, checked against an allowlist "
               "(title, legend, grid, xAxis, yAxis, series[i] styles and markArea/markLine/markPoint, graphic text/line/rect). "
               "series 0 = y1, 1 = y2 (combine: one y1 series per sheet, then one y2 series per sheet). Use only for things no key covers.",
    "grid": "true / false",
    "x|y1|y2.minor": "true for minor ticks between the numbered ones",
    "x|y1|y2.invert": "true to reverse the axis (x: high temperature on the left); x.flip: true means the same",
    "colors": "combine: one colour per sheet or file, in order (a list), or \"mono\"",
    "names": "combine: the legend name of each sheet or file, in order (a list)",
    "offset": "combine: shift each next curve's y1 by this much (e.g. 20), so the curves do not overlap; labels keep the real values",
    "panels": '"split": y1 in an upper panel and y2 in a lower panel with the same x axis',
    "data_code": "Python run in a sandbox before drawing, per sheet: x, y1, y2 (numpy arrays), sheet, np; reassign them "
                 "to change the curve; append {\"type\": \"vline\"|\"hline\"|\"text\", \"x\": .., \"y\": .., \"text\": ..} to marks",
    "asks": 'what the user asked: [{"ask": "...", "how": "key"|"data_code"|"code"|"echarts"|"unsupported"}]',
    "size": "[width, height] in inches (default [6.4, 4.6])",
    "dpi": "resolution of png/jpg (default 300)",
    "font": 'font family; Korean fonts are picked automatically when text is Korean',
    "font_size": "base font size (default 11)",
    "combine": "true = all sheets in ONE figure (one color per sheet)",
    "output.dir": "output folder (default: <data file name>_plots next to the data)",
    "output.format": '"png" (default) | "pdf" | "svg" | "jpg" | "tif", or a list like ["png","pdf"]',
    "output.name": 'file name template; default "{sheet}" ("{file}_{sheet}" for several files)',
}

EXAMPLE_SPEC = {
    "file": "TGA.xlsx",
    "sheets": ["1006R1-V normal"],
    "preset": "tga",
    "x": {"col": "B", "min": 0, "step": 200},
    "y1": {"col": "C", "step": 20},
    "y2": {"col": "D", "step": 0.2},
    "annotate": {
        "residue": {"x": 800, "method": "nearest", "text": "Residue {}%"},
        "peak": {"count": 1},
    },
    "output": {"format": "png"},
}

TOP_ALIASES = {"sheet": "sheets", "sheet_name": "sheets", "sheet_names": "sheets",
               "files": "file", "path": "file", "input": "file",
               "y": "y1", "y_left": "y1", "left": "y1", "yleft": "y1", "y_1": "y1",
               "y_right": "y2", "right": "y2", "yright": "y2", "y_2": "y2",
               "annotations": "annotate", "annotation": "annotate", "labels": "annotate",
               "fontsize": "font_size", "figsize": "size", "figure_size": "size",
               "overlay": "combine", "format": "output.format", "outdir": "output.dir",
               "output_dir": "output.dir", "out": "output.dir", "font_color": "text_color",
               "fontcolor": "text_color", "ticks": "tick_direction", "extra_code": "code",
               "python": "code", "tweak": "code", "echarts_patch": "echarts", "echarts_option": "echarts",
               "x_axis": "x", "xaxis": "x", "x축": "x", "y_axis": "y1", "y1_axis": "y1", "yaxis": "y1",
               "y1axis": "y1", "y축": "y1", "y1축": "y1", "y2_axis": "y2", "y2axis": "y2", "y2축": "y2",
               "secondary_y": "y2", "제목": "title", "그림 제목": "title", "범례": "legend",
               "격자": "grid", "gridlines": "grid", "plot_title": "title", "figure_title": "title",
               "주석": "annotate", "dpi_value": "dpi", "resolution": "dpi", "해상도": "dpi",
               "text_colour": "text_color", "글자 색깔": "text_color", "글자 크기": "font_size",
               "tick_dir": "tick_direction", "틱 방향": "tick_direction", "그림 크기": "size",
               "파일 형식": "output.format", "시트": "sheets", "file_name": "file", "filename": "file",
               "colours": "colors", "palette": "colors", "line_colors": "colors", "legend_names": "names",
               "series_names": "names", "transform": "data_code", "python_data": "data_code",
               "subplots": "panels", "split": "panels", "offsets": "offset", "y_offset": "offset",
               "not_done": "asks"}
AXIS_ALIASES = {"column": "col", "source": "col", "data": "col", "name": "label",
                "title": "label", "tick": "step", "ticks": "step", "tick_step": "step",
                "interval": "step", "unit": "step", "major": "step", "spacing": "step",
                "tick_spacing": "step", "tick_interval": "step", "tickstep": "step", "major_tick": "step",
                "major_ticks": "step", "major_step": "step", "step_size": "step", "tick_gap": "step",
                "틱 간격": "step", "간격": "step", "범위 시작": "min", "범위 끝": "max", "라벨": "label",
                "선 색깔": "color", "색깔": "color", "색": "color", "선 굵기": "width", "굵기": "width",
                "선 종류": "linestyle", "열": "col", "label_text": "label", "axis_label": "label",
                "minimum": "min", "maximum": "max", "lower": "min", "upper": "max",
                "start": "min", "from": "min", "lo": "min", "low": "min", "ymin": "min", "xmin": "min",
                "end": "max", "to": "max", "hi": "max", "high": "max", "ymax": "max", "xmax": "max",
                "colour": "color", "line_width": "width", "linewidth": "width", "lw": "width",
                "ls": "linestyle", "line_style": "linestyle", "dash": "linestyle",
                "legend_label": "legend", "invert": "invert", "sign": "flip", "visible": "show",
                "inverse": "invert", "inverted": "invert", "reverse": "invert", "reversed": "invert",
                "minor_ticks": "minor", "minor_tick": "minor", "보조 눈금": "minor", "보조눈금": "minor",
                "labelsize": "label_size", "label_font_size": "label_size", "fontsize": "label_size",
                "font_size": "label_size", "labelcolor": "label_color", "label_colour": "label_color",
                "ticksize": "tick_size", "tick_label_size": "tick_size", "tick_font_size": "tick_size",
                "tickcolor": "tick_color", "tick_label_color": "tick_color", "tick_colour": "tick_color"}
ANNOT_ALIASES = {"opacity": "alpha", "x_from": "x_min", "x_to": "x_max", "x_start": "x_min", "x_end": "x_max",
                 "label": "text", "format": "text", "template": "text", "series": "on",
                 "axis": "on", "at": "x", "temperature": "x", "at_x": "x", "n": "count",
                 "mode": "kind", "min_x": "x_min", "max_x": "x_max", "position": "where",
                 "colour": "color", "fontsize": "size", "font_size": "size"}

KOREAN_COLORS = {"빨강": "red", "빨간색": "red", "빨간": "red", "적색": "red",
                 "파랑": "blue", "파란색": "blue", "파란": "blue", "청색": "blue",
                 "남색": "navy", "초록": "green", "초록색": "green", "녹색": "green",
                 "검정": "black", "검정색": "black", "검은색": "black", "흑색": "black",
                 "회색": "gray", "주황": "orange", "주황색": "orange", "노랑": "gold",
                 "노란색": "gold", "보라": "purple", "보라색": "purple", "분홍": "hotpink",
                 "분홍색": "hotpink", "갈색": "saddlebrown", "하늘색": "deepskyblue"}
LINESTYLES = {"solid": "-", "실선": "-", "-": "-", "dashed": "--", "파선": "--", "--": "--",
              "dotted": ":", "점선": ":", ":": ":", "dashdot": "-.", "일점쇄선": "-.", "-.": "-."}

LINESTYLE_NAMES = {"-": "solid", "--": "dashed", ":": "dotted", "-.": "dashdot"}


def linestyle_name(v, where):
    """A line style in any spelling plotkit accepts ("--", "점선", "dotted", ...) as solid, dashed, dotted or dashdot.
    Both engines read only these four names, so a spelling draws the same everywhere."""
    ls = str(v).strip().lower()
    if ls not in LINESTYLES:
        raise PlotkitError(f"{where} {v!r} unknown", "use solid, dashed, dotted or dashdot")
    return LINESTYLE_NAMES[LINESTYLES[ls]]


LEGEND_PLACES = ["best", "upper right", "upper left", "lower left", "lower right", "right",
                 "center left", "center right", "lower center", "upper center", "center", "none",
                 "outside right", "outside bottom"]
KOREAN_PLACES = {"오른쪽 위": "upper right", "우상단": "upper right", "왼쪽 위": "upper left",
                 "좌상단": "upper left", "왼쪽 아래": "lower left", "좌하단": "lower left",
                 "오른쪽 아래": "lower right", "우하단": "lower right", "가운데": "center",
                 "왼쪽 가운데": "center left", "오른쪽 가운데": "center right",
                 "위 가운데": "upper center", "아래 가운데": "lower center", "자동": "best",
                 "없음": "none", "숨김": "none", "바깥": "outside right", "밖": "outside right",
                 "그래프 밖": "outside right", "바깥 오른쪽": "outside right", "오른쪽 바깥": "outside right",
                 "그래프 바깥 오른쪽": "outside right", "outside": "outside right", "right outside": "outside right",
                 "바깥 아래": "outside bottom", "아래 바깥": "outside bottom", "bottom outside": "outside bottom",
                 "outside below": "outside bottom", "below": "outside bottom"}

COMBINE_COLORS = ["#1f4e9c", "#c0392b", "#2e8b57", "#d4881c", "#7b3fa0", "#17a2b8",
                  "#8c564b", "#e377c2", "#555555", "#9aa31b"]


def _suggest(key, allowed):
    m = difflib.get_close_matches(key, list(allowed), n=1, cutoff=0.5)
    return f' Did you mean "{m[0]}"?' if m else ""


def _deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _num(v, where):
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        raise PlotkitError(f"{where} must be a number, got {v!r}", "write a plain number, e.g. 200")


def _normalize_axis(name, d):
    if d is False or d is None:
        if name == "y2":
            return {"show": False}
        raise PlotkitError(f"{name} cannot be switched off", "only y2 can be false")
    if isinstance(d, str):          # "x": "B"  -> {"col": "B"}
        d = {"col": d}
    if not isinstance(d, dict):
        raise PlotkitError(f'"{name}" must be an object like {{"col": "B"}}, got {d!r}')
    allowed = set(DEFAULTS[name])
    out = {}
    for k, v in d.items():
        k2 = AXIS_ALIASES.get(k.lower(), k.lower())
        if k2 in ("range", "lim", "limits", "ylim", "xlim"):
            if not (isinstance(v, (list, tuple)) and len(v) == 2):
                raise PlotkitError(f"{name}.{k} must be [min, max]")
            out["min"], out["max"] = v
            continue
        if name == "x" and k2 == "flip":         # x has no data sign: flip means a reversed axis
            k2, v = "invert", v not in (False, None, "none", "no")
        if k2 not in allowed:
            raise PlotkitError(f'unknown key "{name}.{k}".{_suggest(k2, allowed)}',
                               f"allowed keys for {name}: {', '.join(sorted(allowed))}")
        out[k2] = v
    for k in ("minor", "invert"):
        if k in out:
            out[k] = out[k] not in (False, None, "none", "no", 0)
    for k in ("min", "max", "step", "width", "label_size", "tick_size"):
        if k in out:
            out[k] = _num(out[k], f"{name}.{k}")
    for k in ("label_color", "tick_color"):
        if out.get(k) is not None:
            out[k] = _color(out[k], f"{name}.{k}")
    if out.get("step") is not None and out["step"] <= 0:
        raise PlotkitError(f"{name}.step must be > 0")
    if "color" in out and out["color"] is not None:
        out["color"] = _color(out["color"], f"{name}.color")
    if "linestyle" in out:
        out["linestyle"] = linestyle_name(out["linestyle"], f"{name}.linestyle")
    if "style" in out and out["style"] not in ("line", "scatter", "line+marker"):
        raise PlotkitError(f"{name}.style {out['style']!r} unknown", "use line, scatter or line+marker")
    if "flip" in out:
        f = out["flip"]
        f = {True: "flip", False: "none", None: "none", "up": "peaks_up",
             "down": "peaks_down"}.get(f, f)
        if f not in ("none", "flip", "peaks_up", "peaks_down"):
            raise PlotkitError(f"{name}.flip {out['flip']!r} unknown",
                               "use none, flip, peaks_up or peaks_down")
        out["flip"] = f
    return out


def _color(c, where):
    from .colors import is_color_like
    c2 = KOREAN_COLORS.get(str(c).strip(), str(c).strip())
    if re.fullmatch(r"[0-9a-fA-F]{6}", c2):
        c2 = "#" + c2
    if not is_color_like(c2):
        raise PlotkitError(f"{where}: {c!r} is not a color",
                           'use a name like "red", "navy", "black" or a hex code like "#c0392b"')
    return c2


def _guess_annot_type(name):
    n = name.lower()
    if n.startswith(("residue", "value", "res", "잔류", "잔량")):
        return "value_at_x"
    if n.startswith(("peak", "max", "dtg", "피크", "최대")):
        return "peak"
    if n.startswith(("band", "span", "shade", "region", "구간", "음영")):
        return "band"
    for t in ("vline", "hline", "text"):
        if n.startswith(t):
            return t
    return None


def _normalize_annotations(a):
    if a is None or a is False:
        return {}, True
    replace = False
    if isinstance(a, list):         # a list replaces the preset labels completely
        replace = True
        a = {f"{(i.get('type') or 'label') if isinstance(i, dict) else 'label'}_{n}": i
             for n, i in enumerate(a, 1)}
    if not isinstance(a, dict):
        raise PlotkitError('"annotate" must be an object like {"residue": {"x": 800}}')
    out = {}
    for name, d in a.items():
        if d is False or d is None:
            out[name] = None
            continue
        if d is True:                   # "residue": true = asked for, with the preset settings
            out[name] = {}
            continue
        if not isinstance(d, dict):
            raise PlotkitError(f'annotate.{name} must be an object, true or false, got {d!r}')
        dd = {}
        for k, v in d.items():
            k2 = ANNOT_ALIASES.get(k.lower(), k.lower())
            if k2 not in ANNOT_KEYS:
                raise PlotkitError(f'unknown key "annotate.{name}.{k}".{_suggest(k2, ANNOT_KEYS)}',
                                   f"allowed: {', '.join(sorted(ANNOT_KEYS))}")
            dd[k2] = v
        for k in ("x", "y", "x_min", "x_max", "min_rel", "size", "alpha"):
            if k in dd:
                dd[k] = _num(dd[k], f"annotate.{name}.{k}")
        if "count" in dd:
            dd["count"] = int(_num(dd["count"], f"annotate.{name}.count"))
        if "linestyle" in dd:
            dd["linestyle"] = linestyle_name(dd["linestyle"], f"annotate.{name}.linestyle")
        if "on" in dd:
            on = str(dd["on"]).lower()
            on = {"left": "y1", "right": "y2", "y": "y1", "1": "y1", "2": "y2"}.get(on, on)
            if on not in ("y1", "y2"):
                raise PlotkitError(f"annotate.{name}.on must be y1 or y2, got {dd['on']!r}")
            dd["on"] = on
        if "color" in dd and dd["color"] is not None:
            dd["color"] = _color(dd["color"], f"annotate.{name}.color")
        if "type" in dd and dd["type"] not in ANNOT_TYPES:
            raise PlotkitError(f"annotate.{name}.type {dd['type']!r} unknown.{_suggest(str(dd['type']), ANNOT_TYPES)}",
                               f"types: {', '.join(sorted(ANNOT_TYPES))}")
        out[name] = dd
    return out, replace


def normalize_spec(user):
    """Validate a user spec and merge it over defaults (and the preset)."""
    if isinstance(user, str):
        user = {"file": user}
    if not isinstance(user, dict):
        raise PlotkitError("the spec must be a JSON object")
    # map aliases / dotted keys at the top level
    u = {}
    for k, v in user.items():
        k2 = TOP_ALIASES.get(k.lower(), k.lower())
        if "." in k2:
            a, b = k2.split(".", 1)
            u.setdefault(a, {})[b] = v
        elif k2 in u and isinstance(u[k2], dict) and isinstance(v, dict):
            u[k2].update(v)
        else:
            u[k2] = v
    unknown = [k for k in u if k not in DEFAULTS]
    if unknown:
        k = unknown[0]
        k_ax = AXIS_ALIASES.get(k, k)
        if k_ax in DEFAULTS["y1"] or k_ax in ("range", "lim"):
            raise PlotkitError(f'"{k}" belongs to an axis, not the top level',
                               f'put it inside "x", "y1" or "y2", e.g. "x": {{"{k_ax}": ...}}')
        k_an = ANNOT_ALIASES.get(k, k)
        if k_an in ANNOT_KEYS or re.match(r"(residue|peak|vline|hline|note)", k):
            raise PlotkitError(f'"{k}" belongs inside "annotate"',
                               'e.g. "annotate": {"residue": {"x": 700}} or "annotate": {"vline1": {"type": "vline", "x": 450}}')
        raise PlotkitError(f'unknown key "{k}".{_suggest(k, DEFAULTS)}',
                           "top-level keys: " + ", ".join(DEFAULTS))
    if not u.get("file"):
        raise PlotkitError('"file" is missing', 'add "file": "your_data.xlsx"')

    preset = str(u.get("preset", DEFAULTS["preset"]) or "none").lower()
    if preset not in ("tga", "none"):
        raise PlotkitError(f'preset {preset!r} unknown', 'use "tga" or "none"')

    spec = copy.deepcopy(DEFAULTS)
    if preset == "tga":
        p = copy.deepcopy(TGA_PRESET)
        for ax in ("x", "y1", "y2"):
            spec[ax].update(p[ax], _preset_label=True)
        spec["annotate"] = p["annotate"]
        for d in spec["annotate"].values():
            d["_preset_text"] = True
    spec["preset"] = preset

    for ax in ("x", "y1", "y2"):
        if ax in u:
            n = _normalize_axis(ax, u[ax])
            spec[ax].update(n)
            if "label" in n:
                spec[ax].pop("_preset_label", None)
    if "annotate" in u:
        ann, replace = _normalize_annotations(u["annotate"])
        base = {} if replace else spec["annotate"]
        for name, d in ann.items():
            if d is None:
                base.pop(name, None)
            else:                       # named in the user's spec: say "no data" instead of hiding it
                base[name] = {**base.get(name, {}), **d, "_requested": True}
                if "text" in d:
                    base[name].pop("_preset_text", None)
        spec["annotate"] = base
    for name, d in spec["annotate"].items():
        d.setdefault("type", _guess_annot_type(name))
        if d["type"] is None:
            raise PlotkitError(f'annotate.{name} needs a "type"',
                               f"types: {', '.join(sorted(ANNOT_TYPES))}")
        need = {"value_at_x": "x", "vline": "x", "hline": "y"}.get(d["type"])
        if need and d.get(need) is None:
            raise PlotkitError(f'annotate.{name} needs "{need}"',
                               f'e.g. "annotate": {{"{name}": {{"{need}": 800}}}}')
        if d["type"] == "band":
            if d.get("x_min") is None or d.get("x_max") is None:
                raise PlotkitError(f'annotate.{name} (band) needs "x_min" and "x_max"',
                                   f'e.g. "annotate": {{"{name}": {{"type": "band", "x_min": 300, "x_max": 450}}}}')
            if d["x_max"] <= d["x_min"]:
                raise PlotkitError(f"annotate.{name}: x_max must be larger than x_min")
            if d.get("alpha") is not None and not 0 <= d["alpha"] <= 1:
                raise PlotkitError(f"annotate.{name}.alpha must be between 0 and 1", "e.g. 0.15")
    for k in ("read", "output"):
        if k in u:
            if not isinstance(u[k], dict):
                raise PlotkitError(f'"{k}" must be an object')
            for kk in u[k]:
                if kk not in DEFAULTS[k]:
                    raise PlotkitError(f'unknown key "{k}.{kk}".{_suggest(kk, DEFAULTS[k])}',
                                       f"allowed: {', '.join(DEFAULTS[k])}")
            spec[k].update(u[k])
    for k in ("file", "sheets", "grid", "size", "dpi", "font", "font_size", "combine",
              "text_color", "tick_direction", "code", "data_code", "asks", "names", "offset", "panels"):
        if k in u:
            spec[k] = u[k]
    if u.get("colors") is not None:
        c = u["colors"]
        if isinstance(c, str) and c.lower() in ("mono", "흑백", "bw", "black and white", "grayscale"):
            c = ["black", "#666666", "#999999", "#333333", "#bbbbbb", "#555555"]
        if isinstance(c, dict):
            c = list(c.values())
        c = c if isinstance(c, list) else [c]
        spec["colors"] = [_color(x, f"colors[{i}]") for i, x in enumerate(c)]
    if spec["names"] is not None and not isinstance(spec["names"], list):
        spec["names"] = [spec["names"]]
    if spec["offset"] is not None:
        spec["offset"] = _num(spec["offset"], "offset")
    if spec["panels"] not in (None, False):
        pv = str(spec["panels"]).lower()
        if pv in ("true", "split", "stacked", "2", "two", "위아래", "separate", "subplots", "vertical"):
            spec["panels"] = "split"
        else:
            raise PlotkitError(f'panels {spec["panels"]!r} unknown', 'use "split" (y1 above, y2 below)')
    else:
        spec["panels"] = None
    if isinstance(spec["data_code"], list):
        spec["data_code"] = "\n".join(spec["data_code"])
    if not isinstance(spec["asks"], list):
        spec["asks"] = [spec["asks"]]
    if u.get("echarts") not in (None, {}, False):
        from .echarts import validate_patch               # the allowlist lives with the engine
        spec["echarts"] = validate_patch(u["echarts"])
    if "title" in u:
        t = u["title"]
        if t is None or t is False:
            t = {"text": ""}
        if isinstance(t, str):
            t = {"text": t}
        if not isinstance(t, dict):
            raise PlotkitError('"title" must be text or {"text": ..., "size": ..., "color": ...}')
        t = {{"label": "text", "fontsize": "size", "font_size": "size", "colour": "color"}.get(k, k): v
             for k, v in t.items()}
        for k in t:
            if k not in ("text", "size", "color"):
                raise PlotkitError(f'unknown key "title.{k}"', "title keys: text, size, color")
        spec["title"].update(t)
    if "legend" in u:
        lg = u["legend"]
        if lg is False or lg is None or lg == "none":
            lg = {"show": False}
        elif lg is True:
            lg = {"show": True}
        elif isinstance(lg, str):
            lg = {"where": lg}
        if not isinstance(lg, dict):
            raise PlotkitError('"legend" must be a position text, false, or {"where": ..., "show": ..., "size": ...}')
        lg = {{"position": "where", "loc": "where", "location": "where", "fontsize": "size",
               "font_size": "size", "visible": "show"}.get(k, k): v for k, v in lg.items()}
        for k in lg:
            if k not in ("where", "show", "size"):
                raise PlotkitError(f'unknown key "legend.{k}"', "legend keys: where, show, size")
        spec["legend"].update(lg)
    spec["legend"]["where"] = KOREAN_PLACES.get(spec["legend"]["where"], spec["legend"]["where"])
    if spec["legend"]["where"] == "none":
        spec["legend"]["show"] = False
    if spec["legend"]["where"] not in LEGEND_PLACES:
        raise PlotkitError(f'legend position {spec["legend"]["where"]!r} unknown',
                           "use one of: " + ", ".join(LEGEND_PLACES))
    if spec["title"].get("color"):
        spec["title"]["color"] = _color(spec["title"]["color"], "title.color")
    spec["text_color"] = _color(spec["text_color"] or "black", "text_color")
    spec["_text_color_set"] = bool(u.get("text_color"))   # then it also beats the line colours
    td = {"안쪽": "in", "바깥쪽": "out", "밖": "out", "안": "in", "양쪽": "inout"}.get(
        str(spec["tick_direction"]), str(spec["tick_direction"]).lower())
    if td not in ("in", "out", "inout"):
        raise PlotkitError(f"tick_direction {spec['tick_direction']!r} unknown", "use in, out or inout")
    spec["tick_direction"] = td
    if isinstance(spec["code"], list):
        spec["code"] = "\n".join(spec["code"])
    spec["file"] = expand_files(spec["file"] if isinstance(spec["file"], list) else [spec["file"]])
    spec["output"]["format"] = output_formats(spec["output"]["format"])
    return spec


def expand_files(files):
    """File names with * or ? become the matching files, sorted; others stay as they are."""
    import glob
    out = []
    for f in files:
        f = str(f)
        if any(c in f for c in "*?["):
            hits = sorted(glob.glob(f))
            if not hits:
                raise PlotkitError(f"no file matches {f}", "check the folder and the pattern")
            out += hits
        else:
            out.append(f)
    return out


# =================================================================== reading
_NUM_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def _to_num(v, decimal="."):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else None
    if not isinstance(v, str):
        return None                                 # dates, times, ...
    s = v.strip().replace("−", "-").replace(" ", "")
    if not s:
        return None
    if decimal == ",":
        s = s.replace(".", "").replace(",", ".")
    if not _NUM_RE.match(s):
        return None
    return float(s)


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def col_index(letter):
    n = 0
    for ch in letter.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _decode(raw, encoding=None):
    if encoding:
        return raw.decode(encoding)
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw[3:].decode("utf-8")
    head = raw[:2000]
    if head.count(b"\x00") > len(head) // 4:       # utf-16 without BOM
        return raw.decode("utf-16-le" if head[1:2] == b"\x00" else "utf-16-be")
    for enc in ("utf-8", "cp949", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def _read_text(path, ro):
    text = _decode(Path(path).read_bytes(), ro.get("encoding"))
    lines = text.splitlines()
    nonblank = [ln for ln in lines if ln.strip()]
    tail = nonblank[-60:] if len(nonblank) > 60 else nonblank
    sep = ro.get("sep")
    sep = {"tab": "\t", "\\t": "\t", "space": "space", "whitespace": "space", " ": "space"}.get(sep, sep)
    if sep is None:                                 # the most lines with the same count wins (preamble/footer lines may differ)
        for cand in ("\t", ";", ",", "|"):
            counts = [ln.count(cand) for ln in tail]
            if counts:
                mode = max(set(counts), key=counts.count)
                if mode >= 1 and counts.count(mode) >= 0.7 * len(counts):
                    sep = cand
                    break
        sep = sep or "space"
    decimal = ro.get("decimal")
    if decimal is None:
        sample = re.sub(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b|\b\d{1,2}:\d{2}(:\d{2})?\b", " ", " ".join(tail))
        decimal = "," if (sep != "," and re.search(r"(?<![\d.])-?\d+,\d+(?![\d.])", sample)
                          and not re.search(r"\d\.\d", sample)) else "."
    rows = []
    for ln in lines:
        if not ln.strip():
            rows.append([])
            continue
        if sep == "space":
            parts = ln.strip().split()
            nums = sum(_to_num(p, decimal) is not None for p in parts)
            if nums < len(parts):                    # header line: split on 2+ spaces
                parts = re.split(r"\s{2,}|\t", ln.strip())
        else:
            parts = [p.strip().strip('"') for p in ln.split(sep)]
        rows.append(parts)
    return {Path(path).stem: rows}, decimal


def _read_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        out[ws.title] = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return out


def _read_xls(path):
    try:
        import xlrd
    except ImportError:
        raise PlotkitError("reading old .xls files needs the xlrd package",
                           "run: pip install xlrd   (or save the file as .xlsx)")
    book = xlrd.open_workbook(path)
    out = {}
    for sh in book.sheets():
        out[sh.name] = [[None if c == "" else c for c in sh.row_values(i)]
                        for i in range(sh.nrows)]
    return out


def read_tables(path, ro=None):
    """Return {sheet_name: raw rows}, decimal mark."""
    ro = ro or {}
    p = Path(path)
    if not p.exists():
        near = [f.name for f in p.parent.glob("*") if f.is_file()][:20] if p.parent.exists() else []
        raise PlotkitError(f"file not found: {path}",
                           f"files in {p.parent}: {', '.join(near)}" if near else "check the path")
    ext = p.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return _read_xlsx(p), "."
    if ext == ".xls":
        try:
            return _read_xls(p), "."
        except PlotkitError:
            raise
        except Exception:                            # some ".xls" are really text/html
            return _read_text(p, ro)
    return _read_text(p, ro)


def analyze_table(rows, decimal=".", header_row=None, data_start_row=None):
    """Find header and numeric block. Returns dict with columns + data."""
    width = max((len(r) for r in rows), default=0)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    nums = [[_to_num(c, decimal) for c in r] for r in rows]
    ncount = [sum(n is not None for n in r) for r in nums]
    if not rows or max(ncount, default=0) == 0:
        raise PlotkitError("no numbers found in this sheet")

    if data_start_row:
        ds = int(data_start_row) - 1
    elif header_row:
        ds = int(header_row)
        while ds < len(rows) and ncount[ds] < 2:
            ds += 1
    else:
        wide = [c for c in ncount if c >= 2] or [c for c in ncount if c >= 1]
        w = max(set(wide), key=wide.count)
        ds = None
        for i, c in enumerate(ncount):
            if c >= w:
                nxt = [ncount[j] for j in range(i + 1, min(len(rows), i + 40)) if ncount[j] or any(rows[j])][:5]
                if all(n >= max(1, w - 1) for n in nxt):
                    ds = i
                    break
        if ds is None:
            ds = next(i for i, c in enumerate(ncount) if c == w)
    if ds >= len(rows):
        raise PlotkitError("data start row is after the end of the sheet")

    body = nums[ds:]
    body_rows = [r for r in body if any(v is not None for v in r)]
    data_cols = [j for j in range(width)
                 if sum(r[j] is not None for r in body_rows) >= 0.5 * max(1, len(body_rows))]
    if not data_cols:
        raise PlotkitError("no numeric columns found")

    def is_textual(r):
        cells = [rows[r][j] for j in data_cols]
        txt = sum(1 for c in cells if c is not None and str(c).strip() != "" and _to_num(c, decimal) is None)
        return txt >= max(1, math.ceil(len(data_cols) / 2))

    hdr_rows = []
    if header_row:
        hdr_rows = [int(header_row) - 1]
    else:
        i = ds - 1
        while i >= 0 and len(hdr_rows) < 2:
            if not any(c is not None and str(c).strip() for c in rows[i]):
                if hdr_rows:
                    break
                i -= 1
                continue
            if is_textual(i):
                hdr_rows.insert(0, i)
                i -= 1
            else:
                break
        if len(hdr_rows) == 2 and not _looks_like_units(rows[hdr_rows[1]], data_cols):
            hdr_rows = hdr_rows[1:]                 # upper row is a title, not names

    columns = []
    for j in data_cols:
        parts = []
        for r in hdr_rows:
            c = rows[r][j]
            if c is not None and str(c).strip():
                parts.append(str(c).strip())
        name = " ".join(parts)
        vals = np.array([r[j] if r[j] is not None else np.nan for r in body], dtype=float)
        columns.append({"letter": col_letter(j), "index": j, "name": name, "values": vals})
    return {"columns": columns, "header_rows": [r + 1 for r in hdr_rows],
            "data_start_row": ds + 1, "n_rows": len(body_rows)}


def _looks_like_units(row, cols):
    cells = [str(row[j]).strip() for j in cols if row[j] is not None and str(row[j]).strip()]
    if not cells:
        return False
    unit = re.compile(r"^[\(\[]?\s*(%|°c|℃|c|k|min|s|sec|h|mg|g|µg|ug|mw|w/g|mw/mg|%/°c|%/c|%/min|mg/min|°c/min|%/℃|deg\.?c|1/°c)\s*[\)\]]?$", re.I)
    return sum(bool(unit.match(c)) for c in cells) >= 0.5 * len(cells)


# ---------------------------------------------------------- column matching
def _norm(s):
    return re.sub(r"[\s._\-:·,]+", "", str(s).lower())


def _base(s):
    return _norm(re.sub(r"[\(\[\{].*?[\)\]\}]", "", str(s)))


def find_column(table, query, where):
    cols = table["columns"]
    q = str(query).strip()
    q = re.sub(r"^(col(umn)?\s*)|(\s*(열|행|column|col|컬럼|칸))$", "", q, flags=re.I).strip()
    if re.fullmatch(r"[A-Za-z]{1,2}", q):
        idx = col_index(q)
        max_idx = max(c["index"] for c in cols)
        if idx <= max_idx:
            for c in cols:
                if c["index"] == idx:
                    return c
            raise PlotkitError(f"{where}: column {q.upper()} has no numbers",
                               "columns with numbers: " + _col_list(cols))
    qn, qb = _norm(q), _base(q)
    if not qn:
        raise PlotkitError(f"{where}: empty column name")
    scored = []
    for c in cols:
        n, b = _norm(c["name"]), _base(c["name"])
        if not n:
            continue
        s = 0
        if b == qb or n == qn:
            s = 3
        elif n.startswith(qn) or (qb and b.startswith(qb)):
            s = 2
        elif qn in n or (qb and qb in n):
            s = 1
        if s:
            scored.append((s, c))
    if not scored:
        raise PlotkitError(f'{where}: no column matches "{query}"',
                           "use a letter or part of one of these names: " + _col_list(cols))
    top = max(s for s, _ in scored)
    best = [c for s, c in scored if s == top]
    if len(best) > 1:
        raise PlotkitError(f'{where}: "{query}" matches several columns: ' + _col_list(best),
                           "use the column letter instead")
    return best[0]


def _col_list(cols):
    return ", ".join(f'{c["letter"]} "{c["name"] or "(no name)"}"' for c in cols)


ROLE_PATTERNS = [
    ("y2", [r"deriv", r"dtg", r"\bd\.?\s*w\b", r"dw/?dt", r"미분", r"%\s*/\s*(°|℃|c\b|min|deg)", r"/\s*(°c|℃)"]),
    ("time", [r"time", r"시간", r"^\s*t\s*\(\s*(min|s)\s*\)", r"\(\s*(min|s|sec)\s*\)\s*$"]),
    ("x", [r"temp", r"온도", r"^\s*t\s*(\(|$)", r"(°c|℃)"]),
    ("y1", [r"weight", r"\bwt", r"mass", r"무게", r"중량", r"질량", r"^\s*tg\b", r"\(\s*%\s*\)", r"^\s*%\s*$"]),
]


def guess_tga_columns(table):
    """Guess x (temperature), y1 (weight), y2 (DTG) by names, then by values."""
    cols = table["columns"]
    roles = {"x": [], "y1": [], "y2": [], "time": []}
    for c in cols:
        name = c["name"].lower()
        if not name:
            continue
        for role, pats in ROLE_PATTERNS:
            if any(re.search(p, name) for p in pats):
                roles[role].append(c)
                break
    pick = {}
    if roles["x"]:
        pick["x"] = next((c for c in roles["x"] if "sample" in c["name"].lower()), roles["x"][0])
    if roles["y1"]:
        pick["y1"] = next((c for c in roles["y1"] if "%" in c["name"]), roles["y1"][0])
    if roles["y2"]:
        pick["y2"] = next((c for c in roles["y2"] if re.search(r"°c|℃|/c\b", c["name"].lower())),
                          roles["y2"][0])
    how = "by name"
    if len(pick) < 3:                               # fill gaps from the values
        how = "by name and values" if pick else "by values"
        used = {id(c) for c in pick.values()}
        free = [c for c in cols if id(c) not in used]
        if "x" not in pick:
            cand = []
            for c in free:
                v = c["values"][np.isfinite(c["values"])]
                if len(v) > 10:
                    inc = np.mean(np.diff(v) > 0)
                    if inc > 0.7 and 150 <= v.max() <= 2000 and v.min() < 200:
                        cand.append((inc, c))
            if cand:
                pick["x"] = max(cand, key=lambda t: t[0])[1]
        free = [c for c in free if c is not pick.get("x")]
        if "y1" not in pick:
            cand = []
            for c in free:
                v = c["values"][np.isfinite(c["values"])]
                if len(v) > 10 and 50 <= v[:5].mean() <= 110 and v[-5:].mean() < v[:5].mean():
                    cand.append(c)
            if cand:
                pick["y1"] = cand[0]
        free = [c for c in free if c is not pick.get("y1")]
        if "y2" not in pick and "x" in pick and "y1" in pick:
            best, bestr = None, 0.6
            T, W = pick["x"]["values"], pick["y1"]["values"]
            ok = np.isfinite(T) & np.isfinite(W)
            if ok.sum() > 10:
                with np.errstate(all="ignore"):
                    g = np.gradient(W[ok], T[ok])
                for c in free:
                    v = c["values"][ok]
                    m = np.isfinite(v) & np.isfinite(g)
                    if m.sum() > 10 and np.std(v[m]) > 0:
                        r = abs(np.corrcoef(v[m], g[m])[0, 1])
                        if r > bestr:
                            best, bestr = c, r
            if best is not None:
                pick["y2"] = best
    return pick, how


# =================================================================== loading
def load_sheets(spec_or_file, ro=None):
    """Yield (file, sheet_name, table) for every selected sheet."""
    files = spec_or_file["file"] if isinstance(spec_or_file, dict) else [spec_or_file]
    ro = (spec_or_file.get("read") if isinstance(spec_or_file, dict) else ro) or {}
    sel = spec_or_file.get("sheets", "all") if isinstance(spec_or_file, dict) else "all"
    out = []
    for f in files:
        tables, decimal = read_tables(f, ro)
        names = list(tables)
        chosen = _select_sheets(names, sel, f)
        for n in chosen:
            try:
                t = analyze_table(tables[n], decimal, ro.get("header_row"), ro.get("data_start_row"))
            except PlotkitError as e:
                if sel in ("all", None) and len(chosen) > 1:
                    out.append((f, n, PlotkitError(e.message, e.hint)))
                    continue
                raise PlotkitError(f'{Path(f).name} / sheet "{n}": {e.message}', e.hint)
            out.append((f, n, t))
    return out


def _select_sheets(names, sel, f):
    if sel in ("all", None, "", "*"):
        return names
    sel = sel if isinstance(sel, list) else [sel]
    chosen = []
    for s in sel:
        if isinstance(s, str) and s.strip().isdigit() and s not in names:
            s = int(s)
        if isinstance(s, (int, float)) and not isinstance(s, bool):
            i = int(s)
            if not 1 <= i <= len(names):
                raise PlotkitError(f"sheet number {i} does not exist in {Path(f).name}",
                                   f"it has {len(names)} sheet(s): {names}")
            chosen.append(names[i - 1])
            continue
        hit = [n for n in names if n == s] or \
              [n for n in names if _norm(n) == _norm(s)] or \
              [n for n in names if _norm(s) in _norm(n)]
        if len(hit) != 1:
            m = difflib.get_close_matches(str(s), names, n=3, cutoff=0.3)
            raise PlotkitError(
                f'sheet "{s}" {"is ambiguous" if hit else "not found"} in {Path(f).name}',
                f"sheet names: {names}" + (f"; closest: {m}" if m else ""))
        chosen.append(hit[0])
    return chosen


# =================================================================== analysis
def _flip(v, mode):
    if mode == "flip":
        return -v
    if mode in ("peaks_up", "peaks_down"):
        f = v[np.isfinite(v)]
        if not len(f):
            return v
        up = abs(f.max()) >= abs(f.min())
        v = v if up else -v
        return v if mode == "peaks_up" else -v
    return v


def value_at_x(X, Y, x0, method):
    ok = np.isfinite(X) & np.isfinite(Y)
    X, Y = X[ok], Y[ok]
    if not len(X) or x0 < X.min() - 1e-9 or x0 > X.max() + 1e-9:
        return None, None
    if method == "interp":
        keep = np.r_[True, np.diff(np.maximum.accumulate(X)) > 0]
        return float(x0), float(np.interp(x0, X[keep], Y[keep]))
    i = int(np.argmin(np.abs(X - x0)))
    return float(X[i]), float(Y[i])


def find_peaks_xy(X, Y, count=1, kind="max", x_min=None, x_max=None, min_rel=0.1):
    from scipy.signal import find_peaks, savgol_filter
    ok = np.isfinite(X) & np.isfinite(Y)
    X, Y = X[ok], Y[ok]
    y = Y if kind == "max" else -Y
    n = len(y)
    ys = y.copy()
    win = max(5, (n // 100) | 1)
    if win < n:
        ys = savgol_filter(y, win, 2)
    valid = np.ones(n, bool)
    if x_min is not None:
        valid &= X >= x_min
    if x_max is not None:
        valid &= X <= x_max
    if not valid.any():
        return []
    base = np.nanmedian(ys[valid])
    top = ys[valid].max()
    span = top - base
    if span <= 0:
        return []
    idx, _ = find_peaks(ys, height=base + min_rel * span, prominence=0.5 * min_rel * span)
    idx = [i for i in idx if valid[i]]
    if not idx:
        idx = [int(np.argmax(np.where(valid, ys, -np.inf)))]
    idx = sorted(idx, key=lambda i: ys[i], reverse=True)[:max(1, count)]
    return sorted([(float(X[i]), float(Y[i])) for i in idx])


def _fmt(text, x, y, primary):
    """Fill a label template. {} gets the main value, {x} and {y} are numbers."""
    if text is None:
        return ""
    t = text
    if "{}" in t:
        pv = x if primary == "x" else y
        t = t.replace("{}", f"{pv:.0f}" if primary == "x" else f"{pv:.1f}")
    try:
        return t.format(x=x if x is not None else float("nan"),
                        y=y if y is not None else float("nan"))
    except (KeyError, IndexError, ValueError) as e:
        raise PlotkitError(f"label template {text!r} is invalid ({e})",
                           'use {x}, {y} or {}, e.g. "Residue {y:.1f}%"')


# =================================================================== plotting
def _setup_fonts(spec, texts):
    import matplotlib
    from matplotlib import font_manager
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["font.size"] = spec["font_size"]
    matplotlib.rcParams["font.family"] = matplotlib.rcParamsOrig["font.family"]
    if spec["font"]:
        matplotlib.rcParams["font.family"] = [spec["font"], "DejaVu Sans"]
        return None
    if not any(re.search(r"[가-힣ㄱ-ㆎ]", t or "") for t in texts):
        return None
    korean = ("Malgun Gothic", "AppleGothic", "Apple SD Gothic Neo", "NanumGothic",
              "Noto Sans CJK KR", "Noto Sans KR", "Gulim", "Batang", "UnDotum")
    for attempt in range(2):
        have = {f.name for f in font_manager.fontManager.ttflist}
        for f in korean:
            if f in have:
                matplotlib.rcParams["font.family"] = [f, "DejaVu Sans"]
                return None
        if attempt == 0:                 # a font installed after matplotlib's cache was built
            for fp in font_manager.findSystemFonts():
                if re.search(r"nanum|malgun|applegothic|applesdgothic|notosanscjk|notosanskr|gulim",
                             Path(fp).name.lower().replace("-", "").replace("_", "")):
                    try:
                        font_manager.fontManager.addfont(fp)
                    except Exception:  # noqa: BLE001
                        pass
    return "Korean text found but no Korean font is installed; Korean letters may show as boxes"


def _apply_axis(ax, which, axspec, data_min, data_max, pad_lo, pad_hi, tight=False):
    from matplotlib.ticker import MultipleLocator
    lo, hi = axspec.get("min"), axspec.get("max")
    rng = (data_max - data_min) or 1.0
    if lo is None:
        lo = data_min if tight else data_min - pad_lo * rng
    if hi is None:
        hi = data_max if tight else data_max + pad_hi * rng
    if hi <= lo:
        raise PlotkitError(f"axis range is empty (min {lo} >= max {hi})")
    setlim = ax.set_xlim if which == "x" else ax.set_ylim
    if axspec.get("log"):
        (ax.set_xscale if which == "x" else ax.set_yscale)("log")
    setlim(lo, hi)
    step = axspec.get("step")
    if step and not axspec.get("log"):
        if (hi - lo) / step > 60:
            raise PlotkitError(f"step {step} is too small for range {lo:g}..{hi:g}",
                               "use a larger step")
        loc = MultipleLocator(step, offset=(axspec["min"] % step) if axspec.get("min") is not None else 0.0)
        (ax.xaxis if which == "x" else ax.yaxis).set_major_locator(loc)


def _draw_series(ax, X, Y, s, color, label):
    ls = LINESTYLES[s.get("linestyle", "solid")]
    st = s.get("style", "line")
    if st == "scatter":
        return ax.scatter(X, Y, s=8, color=color, label=label)
    marker = "o" if st == "line+marker" else None
    return ax.plot(X, Y, color=color, lw=s.get("width", 1.5), ls=ls, marker=marker,
                   ms=3, label=label)[0]


LABEL_BOX = dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85)


def _place_labels(fig, labels, box_peaks=False, obstacles=(), host=None):
    """Draw the residue and peak labels collected by _annotate so that none overlap.

    A single residue label keeps its usual spot, 40 pt above (or below) its point, nudged
    inside the plot if it would stick out. Several (one per sheet when combined) form a column
    beside their points, on the side with room, one line apart and in the same order as the
    points, each with a line to its own marker; the lines then never cross each other or a
    label. "No data" notes join the end of that column. A peak label sits just above its peak
    (below for "min"), and, lowest peak first, moves away only as far as it must to clear the
    labels already drawn and the `obstacles` (e.g. the legend): straight up if that stays in the
    plot, else sideways, with a line back to its peak if it moved. Labels go on the top axes so
    that no curve is drawn over them."""
    from matplotlib.font_manager import FontProperties
    r = fig.canvas.get_renderer()
    top = host or fig.axes[-1]
    area = top.bbox                                # the plot area, display pixels
    pt = fig.dpi / 72                              # points -> display pixels
    gap = 2 * pt
    boxes = [list(o) for o in obstacles]           # drawn labels as [x0, y0, x1, y1] in pixels

    def extent(lab, weight="normal", pad=0.25):
        fp = FontProperties(size=lab["size"], weight=weight)
        lines = [r.get_text_width_height_descent(t or " ", fp, ismath=False) for t in lab["text"].split("\n")]
        pad = pad * fp.get_size_in_points() * pt   # the white box around the text
        w = max(s[0] for s in lines)
        h = lines[0][1] * (1 + 1.2 * (len(lines) - 1))
        return w + 2 * pad, h + 2 * pad, pad

    def hits(b):
        return [o for o in boxes if b[0] < o[2] + gap and o[0] < b[2] + gap and b[1] < o[3] + gap and o[1] < b[3] + gap]

    def clear(b, down):
        """(dx, dy) in pixels that moves box b off everything drawn so far: straight away from the
        data (up, or down for down=True) if that stays in the plot, else the smaller sideways move
        that does; failing both, the straight move."""
        v = list(b)
        for _ in range(len(boxes) + 1):
            hit = hits(v)
            if not hit:
                break
            s = (min(o[1] for o in hit) - gap - v[3]) if down else (max(o[3] for o in hit) + gap - v[1])
            v[1] += s
            v[3] += s
        dy = v[1] - b[1]
        if not dy or (v[1] >= area.y0 if down else v[3] <= area.y1):
            return 0, dy
        best = None
        for side in (-1, 1):
            h = list(b)
            for _ in range(len(boxes) + 1):
                hit = hits(h)
                if not hit:
                    break
                s = (min(o[0] for o in hit) - gap - h[2]) if side < 0 else (max(o[2] for o in hit) + gap - h[0])
                h[0] += s
                h[2] += s
            if not hits(h) and h[0] >= area.x0 and h[2] <= area.x1 and (best is None or abs(h[0] - b[0]) < abs(best)):
                best = h[0] - b[0]
        return (best, 0) if best is not None else (0, dy)

    def value_box(lab, xt, yt, ha, up):
        w, h, pad = extent(lab)
        x0 = {"right": xt + pad - w, "left": xt - pad}.get(ha, xt - w / 2)
        y0 = yt - pad if up else yt + pad - h
        return [x0, y0, x0 + w, y0 + h]

    def value_label(lab, xy, xt, yt, ha, up, arrow=None):
        """Residue label (or no-data note) with its text at pixel (xt, yt), anchored to xy."""
        ax = lab["ax"]
        px, py = ax.transData.transform(xy)
        kw = {} if arrow is None else {"arrowprops": dict(arrowstyle="-", color=lab["color"], lw=0.8, **arrow)}
        top.annotate(lab["text"], xy=xy, xycoords=ax.transData, annotation_clip=True,
                     xytext=((xt - px) / pt, (yt - py) / pt), textcoords="offset points",
                     ha=ha, va="bottom" if up else "top", fontsize=lab["size"],
                     color=lab.get("text_color", lab["color"]), zorder=6, bbox=LABEL_BOX, **kw)
        b = value_box(lab, xt, yt, ha, up)
        boxes.append(b)
        return b[3] - b[1]

    groups = {}
    for lab in labels:
        if lab["kind"] == "value":
            groups.setdefault((id(lab["ax"]), lab["name"]), []).append(lab)
    for grp in groups.values():
        ax = grp[0]["ax"]
        data = [l for l in grp if l["xy"] is not None]
        notes = [l for l in grp if l["xy"] is None]
        if not data:                               # nothing to point at: notes on the right edge
            for lab in notes:
                ax.text(0.98, 0.5 - 0.09 * lab["stack"], lab["text"], transform=ax.transAxes, ha="right",
                        va="center", fontsize=lab["size"], color=lab["color"], zorder=6,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85))
                w, h, pad = extent(lab, pad=0.3)
                xr, yc = ax.transAxes.transform((0.98, 0.5 - 0.09 * lab["stack"]))
                boxes.append([xr + pad - w, yc - h / 2, xr + pad, yc + h / 2])
            continue
        lo, hi = ax.get_ylim()
        xl, xh = ax.get_xlim()
        up = max((l["xy"][1] - lo) / (hi - lo) for l in data) < 0.7
        pts = {id(l): ax.transData.transform(l["xy"]) for l in data}
        if len(data) == 1 and not notes:
            lab = data[0]
            px, py = pts[id(lab)]
            fx = (lab["xy"][0] - xl) / (xh - xl)
            ha = "right" if fx > 0.8 else ("left" if fx < 0.2 else "center")
            xt = px + {"right": 12, "left": -12}.get(ha, 0) * pt
            yt = py + (40 if up else -40) * pt
            b = value_box(lab, xt, yt, ha, up)
            xt += max(0, area.x0 + gap - b[0]) - max(0, b[2] - (area.x1 - gap))   # keep it inside the plot
            dx, dy = clear(value_box(lab, xt, yt, ha, up), not up)
            value_label(lab, lab["xy"], xt + dx, yt + dy, ha, up, arrow={})
            continue
        width = max(extent(l)[0] for l in grp)
        right = max(p[0] for p in pts.values()) + 6 * pt      # left edge of a column right of the points
        left = min(p[0] for p in pts.values()) - 6 * pt       # right edge of a column left of them
        x0, x1 = ax.bbox.x0, ax.bbox.x1
        if right + width <= x1 or (left - width < x0 and x1 - right >= left - x0):
            ha, edge = "left", right
        else:
            ha, edge = "right", left
        near = sorted(data, key=lambda l: pts[id(l)][1], reverse=not up)   # nearest the points first
        y = pts[id(near[-1])][1] + (40 if up else -40) * pt
        for lab in near + notes:
            arrow = {"relpos": (0 if ha == "left" else 1, 0 if up else 1)} if lab["xy"] else None
            h = value_label(lab, lab["xy"] or near[-1]["xy"], edge, y, ha, up, arrow)
            y += (h + gap) if up else -(h + gap)

    peaks = [l for l in labels if l["kind"] == "peak"]
    for lab in sorted(peaks, key=lambda l: l["ax"].transData.transform(l["xy"])[1] * (-1 if l["down"] else 1)):
        down = lab["down"]
        px, py = lab["ax"].transData.transform(lab["xy"])
        w, h, pad = extent(lab, "bold")
        y0 = py - 11 * pt + pad - h if down else py + 9 * pt - pad
        b = [px - w / 2, y0, px + w / 2, y0 + h]
        dx, dy = clear(b, down)
        kw = {"bbox": LABEL_BOX} if box_peaks else {}
        if math.hypot(dx, dy) / pt > 3:
            kw["arrowprops"] = dict(arrowstyle="-", color=lab["color"], lw=0.6, shrinkB=4)
        top.annotate(lab["text"], xy=lab["xy"], xycoords=lab["ax"].transData, annotation_clip=True,
                     xytext=(dx / pt, (-11 if down else 9) + dy / pt), textcoords="offset points", ha="center",
                     va="top" if down else "bottom", fontsize=lab["size"],
                     color=lab.get("text_color", lab["color"]), fontweight="bold", **kw)
        boxes.append([b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy])


def _within(ax, x, y):
    xl, xh = sorted(ax.get_xlim())
    yl, yh = sorted(ax.get_ylim())
    return xl <= x <= xh and yl <= y <= yh


def _annotate(ax_for, name, a, data, color_for, results, labels, sheet, combine_color=None,
              text_color="black", stack=0, cols=None, text_all=False, yoff=0.0):
    """Draw one annotation. Residue and peak labels go to `labels` for _place_labels.

    text_all: the user set text_color, so label text uses it instead of the line colour."""
    t = a["type"]
    on = a.get("on", "y1")
    if t in ("value_at_x", "peak", "hline") and on not in ax_for:
        results.append({"name": name, "sheet": sheet, "skipped": f"{on} is not drawn"})
        return
    ax = ax_for.get(on, ax_for["y1"])
    col = a.get("color") or combine_color or color_for.get(on, text_color)
    tcol = text_color if text_all and not a.get("color") else col
    fs = a.get("size") or "small"
    if t == "value_at_x":
        X, Y = data["x"], data[on]
        xu, yv = value_at_x(X, Y, a["x"], a.get("method", "nearest"))
        if xu is None:
            results.append({"name": name, "sheet": sheet, "x": a["x"], "value": None,
                            "note": f"x={a['x']:g} is outside the data ({np.nanmin(X):.0f}..{np.nanmax(X):.0f})"})
            if a.get("_requested"):     # preset labels with no data are just left out
                labels.append({"kind": "value", "name": name, "ax": ax, "xy": None, "stack": stack,
                               "text": f"{name}: no data at x = {a['x']:g}\n(data ends at {np.nanmax(X):.0f})",
                               "color": text_color if text_all else (combine_color or "gray"), "size": "small"})
            return
        text = a.get("text", "{y:.1f}")
        unit = _unit(cols[on]["name"]) if cols and on in cols else None
        if a.get("_preset_text") and unit and not _same_unit(unit, "%"):   # e.g. a y1 column in mg
            text = text.replace("{y:.1f}%", "{y:.3g} " + unit)
        label = _fmt(text, xu, yv - (yoff if on == "y1" else 0.0), "y")      # offset curves keep their real values
        ax.plot([xu], [yv], "o", ms=6, mfc="white", mec=col, mew=1.6, zorder=5,
                clip_on=not _within(ax, xu, yv))          # whole, even on the edge of the plot
        labels.append({"kind": "value", "name": name, "ax": ax, "xy": (xu, yv), "text": label,
                       "color": col, "text_color": tcol, "size": fs})
        results.append({"name": name, "sheet": sheet, "x_requested": a["x"], "x_used": round(xu, 3),
                        "value": round(yv - (yoff if on == "y1" else 0.0), 4), "text": label})
    elif t == "peak":
        kind = a.get("kind", "max")
        peaks = find_peaks_xy(data["x"], data[on], a.get("count", 1), kind,
                              a.get("x_min"), a.get("x_max"), a.get("min_rel", 0.1))
        for xp, yp in peaks:
            label = _fmt(a.get("text", "{x:.0f}"), xp, yp, "x")
            ax.plot([xp], [yp], "^" if kind == "max" else "v", ms=6, color=col, zorder=5,
                    clip_on=not _within(ax, xp, yp))
            labels.append({"kind": "peak", "ax": ax, "xy": (xp, yp), "text": label, "color": col,
                           "text_color": tcol, "size": fs, "down": kind != "max"})
        results.append({"name": name, "sheet": sheet, "peaks": [
            {"x": round(xp, 3), "y": round(yp, 5), "text": _fmt(a.get("text", "{x:.0f}"), xp, yp, "x")}
            for xp, yp in peaks]})
    elif t == "vline":
        ax.axvline(a["x"], color=a.get("color") or "gray", lw=0.9,
                   ls=LINESTYLES.get(a.get("linestyle", "dashed"), "--"))
        if a.get("text"):
            ax.annotate(_fmt(a["text"], a["x"], None, "x"), xy=(a["x"], 1), xycoords=("data", "axes fraction"),
                        xytext=(3, -3), textcoords="offset points", ha="left", va="top",
                        fontsize=fs, color=a.get("color") or (text_color if text_all else "gray"))
        results.append({"name": name, "sheet": sheet, "x": a["x"]})
    elif t == "hline":
        ax.axhline(a["y"], color=a.get("color") or "gray", lw=0.9,
                   ls=LINESTYLES.get(a.get("linestyle", "dashed"), "--"))
        if a.get("text"):
            ax.annotate(_fmt(a["text"], None, a["y"], "y"), xy=(0, a["y"]), xycoords=("axes fraction", "data"),
                        xytext=(3, 3), textcoords="offset points", ha="left", va="bottom",
                        fontsize=fs, color=a.get("color") or (text_color if text_all else "gray"))
        results.append({"name": name, "sheet": sheet, "y": a["y"]})
    elif t == "band":
        if stack == 0:                  # once per figure, also when sheets are combined
            ax_for["y1"].axvspan(a["x_min"], a["x_max"], color=a.get("color") or "gray",
                                 alpha=a.get("alpha", 0.15), lw=0, zorder=0)
            if a.get("text"):
                ax_for["y1"].annotate(a["text"], xy=((a["x_min"] + a["x_max"]) / 2, 1),
                                      xycoords=("data", "axes fraction"), xytext=(0, -3),
                                      textcoords="offset points", ha="center", va="top", fontsize=fs,
                                      color=a.get("color") or (text_color if text_all else "gray"))
        results.append({"name": name, "sheet": sheet, "x_min": a["x_min"], "x_max": a["x_max"]})
    elif t == "text" and a.get("x") is not None and a.get("y") is not None:
        tax = ax_for.get(on, ax_for["y1"])
        tax.plot([a["x"]], [a["y"]], "o", ms=3.5, color=a.get("color") or text_color, zorder=5)
        tax.annotate(a.get("text", ""), xy=(a["x"], a["y"]), xytext=(5, 5), textcoords="offset points",
                     ha="left", va="bottom", fontsize=fs, color=a.get("color") or text_color, bbox=LABEL_BOX)
        results.append({"name": name, "sheet": sheet, "text": a.get("text", ""), "x": a["x"], "y": a["y"]})
    elif t == "text":
        where = a.get("where", "upper right")
        pos = {"upper left": (0.02, 0.97, "left", "top"), "upper right": (0.98, 0.97, "right", "top"),
               "lower left": (0.02, 0.03, "left", "bottom"), "lower right": (0.98, 0.03, "right", "bottom"),
               "center": (0.5, 0.5, "center", "center")}.get(where, (0.98, 0.97, "right", "top"))
        ax_for["y1"].text(pos[0], pos[1], a.get("text", ""), transform=ax_for["y1"].transAxes,
                          ha=pos[2], va=pos[3], fontsize=fs, color=a.get("color") or text_color)
        results.append({"name": name, "sheet": sheet, "text": a.get("text", "")})


def _resolve_columns(spec, table, where):
    """Return {role: column dict} and a description."""
    used = {}
    guess, how = (guess_tga_columns(table) if spec["preset"] == "tga" else ({}, ""))
    for role in ("x", "y1", "y2"):
        if role == "y2" and not spec["y2"].get("show", True):
            continue
        q = spec[role].get("col")
        if q not in (None, ""):
            used[role] = find_column(table, q, f"{where} {role}.col")
        elif role in guess:
            used[role] = guess[role]
        elif role == "y2" and spec["preset"] != "tga":
            continue
        else:
            raise PlotkitError(
                f"{where}: could not tell which column is {role}"
                + (" (TGA preset)" if spec["preset"] == "tga" else ""),
                f'set "{role}": {{"col": "<letter>"}}; columns: ' + _col_list(table["columns"]))
    return used, how


def _unit(name):
    """The unit in brackets at the end of a name: "Weight (mg)" -> "mg", "D.W(%/C)" -> "%/C"."""
    m = re.search(r"[(\[]\s*([^()\[\]]+?)\s*[)\]]\s*$", name or "")
    return m.group(1) if m else None


def _same_unit(a, b):
    def norm(u):
        return re.sub(r"[\s°]", "", u.lower().replace("℃", "c"))
    return norm(a) == norm(b)


def _labels(spec, role, col):
    lab = spec[role].get("label")
    if lab is None:
        lab = col["name"] or f"column {col['letter']}"
    elif spec[role].get("_preset_label"):         # the preset's label, but the column says another unit
        mine, theirs = _unit(lab), _unit(col["name"])
        if mine and theirs and not _same_unit(mine, theirs):
            lab = col["name"]
    return lab


def build_jobs(spec):
    """Read the sheets a normalized spec asks for. Returns (jobs, warnings); shared by both engines.

    A job is one sheet: its file, name, the columns used per role and the finite data per role."""
    sheets = load_sheets(spec)
    warnings = []
    jobs = []
    for f, n, t in sheets:
        where = f'{Path(f).name} / "{n}"'
        if isinstance(t, PlotkitError):
            warnings.append(f"skipped {where}: {t.message}")
            continue
        try:
            cols, how = _resolve_columns(spec, t, where)
        except PlotkitError as e:
            if len(sheets) > 1 and spec["sheets"] in ("all", None):
                warnings.append(f"skipped {where}: {e.message}")
                continue
            raise
        data = {}
        for role, c in cols.items():
            v = c["values"].astype(float)
            data[role] = _flip(v, spec[role].get("flip", "none")) if role != "x" else v
        ok = np.isfinite(data["x"])
        for role in data:
            ok &= np.isfinite(data[role])
        if ok.sum() < 3:
            warnings.append(f"skipped {where}: fewer than 3 complete rows")
            continue
        for role in data:
            data[role] = data[role][ok]
        marks = {}
        if spec.get("data_code"):
            data, marks = run_data_code(spec, data, n)
        jobs.append({"file": f, "sheet": n, "cols": cols, "how": how, "data": data,
                     "rows": int(len(data["x"])), "marks": marks, "yoff": 0.0})
    if not jobs:
        raise PlotkitError("nothing to plot", "; ".join(warnings) or "check the file")
    if spec.get("combine") and spec.get("offset"):
        for k, j in enumerate(jobs):
            j["yoff"] = k * spec["offset"]
            j["data"]["y1"] = j["data"]["y1"] + j["yoff"]
    return jobs, warnings


def run_data_code(spec, data, sheet):
    """The spec's data_code on one sheet's arrays, in a sandbox. Returns (data, marks)."""
    from . import sandbox
    names = ["x", "y1", "y2", "marks"]
    out = sandbox.run(spec["data_code"], {"x": data["x"].copy(), "y1": data["y1"].copy(),
                                          "y2": data["y2"].copy() if "y2" in data else None,
                                          "sheet": sheet, "marks": []}, names,
                      hint="names: x, y1, y2 (numpy arrays), sheet, np, marks (a list); reassign x/y1/y2 to change the curve")
    new = {}
    for role in ("x", "y1", "y2"):
        if role not in data:
            continue
        v = out.get(role)
        try:
            v = np.asarray(v, dtype=float).ravel()
        except (TypeError, ValueError):
            raise PlotkitError(f"data_code left {role} as something that is not numbers")
        new[role] = v
    n = len(new["x"])
    for role, v in new.items():
        if len(v) != n:
            raise PlotkitError(f"data_code: {role} has {len(v)} values but x has {n}", "keep x, y1 and y2 the same length")
    ok = np.isfinite(new["x"]) & np.isfinite(new["y1"])
    new = {r: v[ok] for r, v in new.items()}
    raw = out.get("marks") or []
    if not isinstance(raw, list):
        raise PlotkitError("data_code: marks must be a list of dicts")
    marks = {}
    for i, m in enumerate(raw, 1):
        if not isinstance(m, dict):
            raise PlotkitError("data_code: each mark must be a dict like {'type': 'vline', 'x': 605, 'text': 'Onset 605 °C'}")
        m = {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in m.items()}
        ann, _ = _normalize_annotations({f"mark{i}": m})
        d = ann[f"mark{i}"]
        d.setdefault("type", "text")
        need = {"vline": "x", "hline": "y"}.get(d["type"])
        if need and d.get(need) is None:
            raise PlotkitError(f'data_code: a {d["type"]} mark needs "{need}"')
        marks[f"mark{i}"] = d
    return new, marks


def output_target(spec):
    """(output folder, file name template) for a normalized spec; the folder is created."""
    multi_file = len(spec["file"]) > 1
    name_tpl = spec["output"]["name"] or ("{file}_{sheet}" if multi_file else "{sheet}")
    outdir = Path(spec["output"]["dir"] or (Path(spec["file"][0]).with_suffix("").as_posix() + "_plots"))
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir, name_tpl


def figure_title(spec, first):
    title_tpl = spec["title"].get("text") or ""
    if spec["combine"] and title_tpl == "{sheet}":     # several sheets: their names are in the legend; no file-name title
        title_tpl = ""
    return title_tpl.replace("{sheet}", first["sheet"]).replace("{file}", Path(first["file"]).stem)


def file_stem(name_tpl, spec, first):
    fname = name_tpl.replace("{sheet}", "all_sheets" if spec["combine"] else first["sheet"]) \
                    .replace("{file}", Path(first["file"]).stem)
    return re.sub(r'[\\/:*?"<>|\s]+', "_", fname).strip("_") or "plot"


def engine_name(engine=None):
    """The drawing engine: the argument, else $PLOTKIT_ENGINE, else echarts. matplotlib is optional
    (pip install "plotkit[matplotlib]")."""
    import os
    e = str(engine or os.environ.get("PLOTKIT_ENGINE") or "echarts").strip().lower()
    if e not in ENGINES:
        raise PlotkitError(f"unknown engine {e!r}", "use echarts or matplotlib")
    if e == "matplotlib":
        import importlib.util
        if importlib.util.find_spec("matplotlib") is None:
            raise PlotkitError("the matplotlib engine is not installed",
                               'use the ECharts engine, or install it: pip install "plotkit[matplotlib]"')
    return e


def route(user_spec):
    """Where a spec goes: ("chart", spec) when it names a chart (under "chart" or an alias), ("chart", the same plot
    as a chart line) for a curve whose x is a date column (a sensor log), else ("curve", spec)."""
    from . import charts
    if charts.is_chart_spec(user_spec):
        return "chart", user_spec
    if isinstance(user_spec, dict) and user_spec.get("file"):
        alt = charts.curve_as_chart(user_spec)
        if alt:
            return "chart", alt
    return "curve", user_spec


def plot(user_spec, engine=None, *, out_dir=None, formats=None, summary_csv=True):
    """Make the plots. Returns a result dict (also printed as JSON by the CLI).

    engine: "echarts" (default) or "matplotlib" (optional); when None, $PLOTKIT_ENGINE decides.
    out_dir, formats: the host's folder and file formats; they win over the spec's "output" (default: the spec's,
        else a folder <data file>_plots next to the data, PNG).
    summary_csv: also write summary.csv (the residue and peak values) next to curve plots.

    Every result has ok, kind ("curve" | "chart"), engine, saved (the files written), warnings, not_done (the asks
    marked unsupported) and values (the numbers drawn or computed). Curves add output_dir and plots (one entry per
    figure); charts add chart (the chart kind), rows_used, rows_total and summary (Korean)."""
    kind, user_spec = route(user_spec)
    if kind == "chart":
        from . import charts
        return charts.plot(user_spec, engine=engine, out_dir=out_dir, formats=formats)
    if engine_name(engine) == "echarts":
        from .echarts import plot_echarts
        return plot_echarts(user_spec, out_dir=out_dir, formats=formats, summary_csv=summary_csv)
    import warnings as _w
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _w.filterwarnings("ignore", message="Glyph .* missing")
    import logging
    logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

    spec = set_output(normalize_spec(user_spec), out_dir, formats)
    if spec["echarts"]:
        raise PlotkitError('"echarts" only works with the ECharts engine',
                           'this run draws with matplotlib: remove "echarts", or use a key or "code"')
    jobs, warnings = build_jobs(spec)
    outdir, name_tpl = output_target(spec)

    groups = [jobs] if spec["combine"] else [[j] for j in jobs]
    results = []
    for group in groups:
        first = group[0]
        title = figure_title(spec, first)
        texts = [title] + [spec[r].get("label") or "" for r in ("x", "y1", "y2")] + \
                [j["sheet"] for j in group] + [c["name"] for j in group for c in j["cols"].values()] + \
                [a.get("text") or "" for a in spec["annotate"].values()] + [str(n) for n in spec.get("names") or []] + \
                [str(a.get("text") or "") for j in group for a in j.get("marks", {}).values()]
        w = _setup_fonts(spec, texts)
        if w and w not in warnings:
            warnings.append(w)
        tc = spec["text_color"]

        has_y2 = all("y2" in j["data"] for j in group)
        split = bool(spec["panels"]) and has_y2
        if split:
            fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=tuple(spec["size"]), dpi=spec["dpi"],
                                           gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.08})
        else:
            fig, ax1 = plt.subplots(figsize=tuple(spec["size"]), dpi=spec["dpi"])
            ax2 = ax1.twinx() if has_y2 else None
        axes = {"y1": ax1}
        if ax2 is not None:
            axes["y2"] = ax2
        handles = []
        allx = np.concatenate([j["data"]["x"] for j in group])
        for k, j in enumerate(group):
            c1, c2, lab1 = series_style(spec, j, k)
            handles.append(_draw_series(ax1, j["data"]["x"], j["data"]["y1"], spec["y1"], c1, lab1))
            if ax2 is not None:
                s2 = dict(spec["y2"])
                if spec["combine"] and not split:
                    s2["linestyle"] = "dashed"
                lab2 = None if spec["combine"] else (spec["y2"].get("legend") or _labels(spec, "y2", j["cols"]["y2"]))
                h = _draw_series(ax2, j["data"]["x"], j["data"]["y2"], s2, c2, lab2)
                if lab2:
                    handles.append(h)
            j["colors"] = {"y1": c1, "y2": c2}

        # axis labels, ranges, ticks.  y-axis text follows the line color unless set
        # (its own label_color/tick_color, or an explicit text_color for all text).
        def axis_text(role, ax, which):
            a = spec[role]
            line_c = None if (spec["combine"] or role == "x") else a.get("color")
            text_c = tc if spec["_text_color_set"] else (line_c or tc)
            lc = a.get("label_color") or text_c
            kc = a.get("tick_color") or text_c
            setlab = ax.set_xlabel if which == "x" else ax.set_ylabel
            kw = {"color": lc}
            if a.get("label_size"):
                kw["fontsize"] = a["label_size"]
            setlab(_labels(spec, role, first["cols"][role]), **kw)
            tk = {"labelcolor": kc, "color": a.get("tick_color") or line_c or tc}
            if a.get("tick_size"):
                tk["labelsize"] = a["tick_size"]
            ax.tick_params(axis="x" if which == "x" else "y", **tk)
            return line_c

        axis_text("x", ax2 if split else ax1, "x")
        _apply_axis(ax1, "x", spec["x"], np.nanmin(allx), np.nanmax(allx), 0, 0, tight=True)
        y1all = np.concatenate([j["data"]["y1"] for j in group])
        _apply_axis(ax1, "y", spec["y1"], np.nanmin(y1all), np.nanmax(y1all), 0.08, 0.12)
        c_left = axis_text("y1", ax1, "y")
        c_right = None
        if ax2 is not None:
            y2all = np.concatenate([j["data"]["y2"] for j in group])
            _apply_axis(ax2, "y", spec["y2"], np.nanmin(y2all), np.nanmax(y2all), 0.12, 0.18)
            c_right = axis_text("y2", ax2, "y")
            if c_left and not split:
                ax2.spines["left"].set_color(c_left)
            if c_right and not split:
                ax2.spines["right"].set_color(c_right)
        for a in axes.values():
            a.tick_params(direction=spec["tick_direction"])
        _axis_extras(spec, ax1, ax2, split)
        if spec["grid"]:
            ax1.grid(True, alpha=0.3)

        ann_results, labels = [], []
        for k, j in enumerate(group):
            for name, a in list(spec["annotate"].items()) + list(j.get("marks", {}).items()):
                _annotate(axes, name, a, j["data"], j["colors"], ann_results, labels, j["sheet"],
                          combine_color=j["colors"]["y1"] if spec["combine"] else None,
                          text_color=tc, stack=k, cols=j["cols"], text_all=spec["_text_color_set"],
                          yoff=j.get("yoff", 0.0))
        lg = spec["legend"]
        leg = None
        if lg["show"]:
            if spec["combine"] and ax2 is not None:
                from matplotlib.lines import Line2D
                handles = handles + [Line2D([], [], color="gray", ls="-", label=_labels(spec, "y1", first["cols"]["y1"])),
                                     Line2D([], [], color="gray", ls="--", label=_labels(spec, "y2", first["cols"]["y2"]))]
            if lg["where"] == "outside right":
                leg = ax1.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02 if ax2 is None or split else 1.14, 0.5),
                                 frameon=False, fontsize=lg["size"] or "small")
            elif lg["where"] == "outside bottom":
                leg = (ax2 if split else ax1).legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2),
                                                     ncol=min(4, len(handles)), frameon=False, fontsize=lg["size"] or "small")
            else:
                leg = ax1.legend(handles=handles, loc=lg["where"], frameon=False,
                                 fontsize=lg["size"] or "small")
            for t in leg.get_texts():
                t.set_color(tc)
        if title:
            kw = {"color": spec["title"].get("color") or tc}
            if spec["title"].get("size"):
                kw["fontsize"] = spec["title"]["size"]
            ax1.set_title(title, **kw)
        with __import__("warnings").catch_warnings():
            __import__("warnings").simplefilter("ignore")
            fig.tight_layout()                     # final geometry first, so the labels can see the legend
        obstacles = []
        if leg is not None:
            e = leg.get_window_extent(fig.canvas.get_renderer())
            obstacles.append([e.x0, e.y0, e.x1, e.y1])
        if split:                                  # each panel places its own labels
            _place_labels(fig, [l for l in labels if l["ax"] is ax1], box_peaks=spec["combine"], obstacles=obstacles, host=ax1)
            _place_labels(fig, [l for l in labels if l["ax"] is ax2], box_peaks=spec["combine"], host=ax2)
        else:
            _place_labels(fig, labels, box_peaks=spec["combine"], obstacles=obstacles)

        if spec["code"]:
            last = group[-1]
            env = {"fig": fig, "ax1": ax1, "ax2": ax2, "ax": ax1, "plt": plt, "np": np,
                   "x": last["data"]["x"], "y1": last["data"]["y1"], "y2": last["data"].get("y2"),
                   "sheet": last["sheet"], "data": {j["sheet"]: j["data"] for j in group}}
            try:
                exec(compile(spec["code"], "<spec code>", "exec"), env)
            except Exception as e:  # noqa: BLE001 - report any error back to the agent
                plt.close(fig)
                raise PlotkitError(f"the extra code failed: {type(e).__name__}: {e}",
                                   "fix the code; names available: fig, ax1, ax2, x, y1, y2, sheet, plt, np")
        fig.tight_layout()

        fname = file_stem(name_tpl, spec, first)
        outs = []
        if leg is not None and lg["where"].startswith("outside"):
            fit_outside_legend(fig, leg, lg["where"])
        for fmt in spec["output"]["format"]:
            p = outdir / f"{fname}.{fmt}"
            fig.savefig(p, dpi=spec["dpi"])
            outs.append(str(p))
        plt.close(fig)
        results.append({
            "sheet": "all" if spec["combine"] else first["sheet"],
            "file": Path(first["file"]).name,
            "saved": outs,
            "rows_plotted": sum(j["rows"] for j in group),
            "columns_used": {j["sheet"]: {r: f'{c["letter"]} "{c["name"]}"' for r, c in j["cols"].items()}
                             for j in group},
            "column_guess": first["how"] or "as given",
            "annotations": ann_results,
        })
    if summary_csv:
        _write_summary(outdir, results)
    return curve_result("matplotlib", outdir, results, warnings, spec)


def curve_result(engine, outdir, plots, warnings, spec):
    """The result of a curve plot, in the shape chart results share (see plot)."""
    return {"ok": True, "kind": "curve", "engine": engine, "saved": [p for r in plots for p in r["saved"]],
            "warnings": warnings, "not_done": not_done(spec), "values": curve_values(plots),
            "output_dir": str(outdir), "plots": plots}


def curve_values(plots):
    """The numbers plotkit computed for the labels, per sheet: {sheet: {name: {"x", "value"} | [peaks]}}."""
    out = {}
    for r in plots:
        for a in r["annotations"]:
            if "peaks" in a:
                out.setdefault(a["sheet"], {})[a["name"]] = [dict(p) for p in a["peaks"]]
            elif "value" in a:
                out.setdefault(a["sheet"], {})[a["name"]] = {"x": a.get("x_used", a.get("x")), "value": a["value"]}
    return out


FORMATS = ("png", "pdf", "svg", "jpg", "tif")


def output_formats(fmts, key="output.format"):
    """A format or list of formats, checked: ["png", "pdf", ...] (jpeg -> jpg, tiff -> tif)."""
    fmts = [fmts] if isinstance(fmts, str) else list(fmts)
    fmts = [str(f).lower().lstrip(".").replace("jpeg", "jpg").replace("tiff", "tif") for f in fmts]
    for f in fmts:
        if f not in FORMATS:
            raise PlotkitError(f"{key} {f!r} not supported", "use png, pdf, svg, jpg or tif")
    return fmts


def set_output(spec, out_dir=None, formats=None):
    """The host's folder and formats win over the normalized spec's "output" (changed in place and returned)."""
    if out_dir is not None:
        spec["output"]["dir"] = str(out_dir)
    if formats is not None:
        spec["output"]["format"] = output_formats(formats, "format")
    return spec


def fit_outside_legend(fig, leg, where):
    """Shrink the plot so a legend outside it still fits in the figure (the file keeps the asked size)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    for _ in range(4):
        bb = leg.get_window_extent(r).transformed(fig.transFigure.inverted())
        pars = fig.subplotpars
        if where == "outside right":
            over = bb.x1 - 0.99
            if over <= 0:
                break
            fig.subplots_adjust(right=pars.right - over - 0.005)
        else:
            over = 0.01 - bb.y0
            if over <= 0:
                break
            fig.subplots_adjust(bottom=pars.bottom + over + 0.005)
        fig.canvas.draw()


def not_done(spec):
    """The asks the model marked unsupported, to tell the user (curves and charts alike)."""
    return [str(a.get("ask", "")) for a in spec.get("asks") or []
            if isinstance(a, dict) and str(a.get("how", "")).lower() in ("unsupported", "no", "none", "not_done")]


def series_style(spec, j, k):
    """(y1 colour, y2 colour, legend name) of sheet k; shared by both engines."""
    if spec["combine"]:
        cols = spec.get("colors") or COMBINE_COLORS
        c1 = cols[k % len(cols)]
        c2 = c1
        names = spec.get("names") or []
        lab1 = str(names[k]) if k < len(names) else (j["sheet"] if len(spec["file"]) == 1 else
                                                      (Path(j["file"]).stem if len({Path(f).stem for f in spec["file"]}) > 1 else j["sheet"]))
    else:
        cols = spec.get("colors") or []
        c1 = cols[0] if cols else spec["y1"]["color"]
        c2 = cols[1] if len(cols) > 1 else spec["y2"]["color"]
        names = spec.get("names") or []
        lab1 = str(names[0]) if names else (spec["y1"].get("legend") or _labels(spec, "y1", j["cols"]["y1"]))
    return c1, c2, lab1


def _axis_extras(spec, ax1, ax2, split):
    from matplotlib.ticker import AutoMinorLocator
    for role, ax, which in (("x", ax1, "x"), ("y1", ax1, "y"), ("y2", ax2, "y")):
        if ax is None:
            continue
        a = spec[role]
        axis = ax.xaxis if which == "x" else ax.yaxis
        if a.get("minor") and not a.get("log"):
            axis.set_minor_locator(AutoMinorLocator())
            ax.tick_params(axis=which, which="minor", direction=spec["tick_direction"], length=2)
            if split and role == "x":
                ax2.xaxis.set_minor_locator(AutoMinorLocator())
        if a.get("invert"):
            if which == "x":
                ax1.invert_xaxis()           # shared by a twin or a lower panel
            else:
                ax.invert_yaxis()


def _write_summary(outdir, results):
    import csv
    rows = []
    for r in results:
        per = {}
        for a in r["annotations"]:
            d = per.setdefault(a["sheet"], {"file": r["file"], "sheet": a["sheet"], "plot": ";".join(r["saved"])})
            if "peaks" in a:
                d[f"{a['name']}_x"] = "; ".join(f"{p['x']:g}" for p in a["peaks"])
                d[f"{a['name']}_y"] = "; ".join(f"{p['y']:g}" for p in a["peaks"])
            elif "value" in a:
                d[f"{a['name']}_x_used"] = a.get("x_used", "")
                d[f"{a['name']}_value"] = a["value"] if a["value"] is not None else ""
        rows.extend(per.values() or [{"file": r["file"], "sheet": r["sheet"], "plot": ";".join(r["saved"])}])
    keys = []
    for d in rows:
        keys += [k for k in d if k not in keys]
    with open(outdir / "summary.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# =================================================================== inspect
def inspect_file(path, sheets="all", read=None):
    """Describe every sheet: header rows, data rows, columns, TGA guess."""
    spec = {"file": [path], "sheets": sheets, "read": read or {}}
    out = {"ok": True, "file": str(path), "sheets": []}
    for f, n, t in load_sheets(spec):
        if isinstance(t, PlotkitError):
            out["sheets"].append({"name": n, "error": t.message})
            continue
        cols = []
        for c in t["columns"]:
            v = c["values"][np.isfinite(c["values"])]
            cols.append({"col": c["letter"], "name": c["name"] or "(no name)",
                         "first": _r(v[0]) if len(v) else None,
                         "min": _r(v.min()) if len(v) else None,
                         "max": _r(v.max()) if len(v) else None})
        g, how = guess_tga_columns(t)
        out["sheets"].append({
            "name": n,
            "header_rows": t["header_rows"] or "none found",
            "data_start_row": t["data_start_row"],
            "data_rows": t["n_rows"],
            "columns": cols,
            "tga_guess": {r: f'{c["letter"]} "{c["name"]}"' for r, c in g.items()} | {"how": how}
            if len(g) == 3 else f"incomplete ({', '.join(g) or 'nothing'} found); give x/y1/y2 col explicitly",
        })
    return out


def _r(v):
    v = float(v)
    return float(f"{v:.4g}")


# =================================================================== CLI
def dumps(obj):
    """Indented JSON, but small objects/lists stay on one line (short for an LLM)."""
    txt = json.dumps(obj, ensure_ascii=False, indent=1)
    flat = re.compile(r"[\{\[][^\{\}\[\]]*[\}\]]")
    return flat.sub(lambda m: re.sub(r"\s*\n\s*", " ", m.group()), txt)


def _print(obj):
    sys.stdout.write(dumps(obj) + "\n")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    engine = None
    if "--engine" in rest:                 # plot ... --engine echarts  (default: $PLOTKIT_ENGINE or matplotlib)
        i = rest.index("--engine")
        engine = rest[i + 1] if i + 1 < len(rest) else ""
        rest = rest[:i] + rest[i + 2:]
    try:
        if cmd == "inspect":
            if not rest:
                raise PlotkitError("usage: python -m plotkit inspect FILE [--sheet NAME]")
            sheets = "all"
            if "--sheet" in rest:
                i = rest.index("--sheet")
                sheets = rest[i + 1]
                rest = rest[:i] + rest[i + 2:]
            for f in rest:
                _print(inspect_file(f, sheets))
        elif cmd == "plot":
            if not rest:
                raise PlotkitError("usage: python -m plotkit plot SPEC.json | --json '{...}' | DATAFILE")
            if rest[0] == "--json":
                try:
                    spec = json.loads(" ".join(rest[1:]))
                except json.JSONDecodeError as e:
                    raise PlotkitError(f"the JSON is invalid: {e}", "check quotes and commas")
            elif rest[0].lower().endswith(".json"):
                try:
                    spec = json.loads(Path(rest[0]).read_text(encoding="utf-8-sig"))
                except FileNotFoundError:
                    raise PlotkitError(f"spec file not found: {rest[0]}")
                except json.JSONDecodeError as e:
                    raise PlotkitError(f"{rest[0]} is not valid JSON: {e}", "check quotes and commas")
            else:
                spec = {"file": rest[0]}          # plot a data file with the defaults
            _print(plot(spec, engine))
        elif cmd == "schema":
            _print({"keys": SCHEMA_DOC, "defaults": DEFAULTS, "tga_preset": TGA_PRESET})
        elif cmd == "example":
            _print(EXAMPLE_SPEC)
        else:
            raise PlotkitError(f"unknown command {cmd!r}", "use inspect, plot, schema or example")
    except PlotkitError as e:
        _print({"ok": False, "error": e.message, "hint": e.hint})
        return 2
    return 0

