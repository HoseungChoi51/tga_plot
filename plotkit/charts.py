#!/usr/bin/env python3
"""
plotkit.charts - spec-driven charts of table data (bar, line, scatter, histogram, heatmap, pie).

plotkit.core draws instrument curves (TGA and other x-y exports). plotkit.charts draws tables of records,
such as a production run log: it reads the table, filters, groups and aggregates in Python, and
builds one engine-neutral figure model that matplotlib or ECharts then draws. A spec with a "chart"
key goes here (plotkit.plot routes it):

    {"file": "run_log.xlsx", "chart": "bar", "x": "반응기", "y": {"col": "수율", "agg": "mean"}}

    python -m plotkit.charts preview FILE      columns, types, values (what the model sees)
    python -m plotkit.charts plot SPEC.json [--engine echarts]
    python -m plotkit.charts schema

The model writes only the spec. "data_code" (Python on the DataFrame `df`, run in a sandbox before
anything is drawn) covers data changes no key covers; "code" (matplotlib, after drawing) and
"echarts" (a checked option patch) cover drawing changes on one engine only.
"""
import copy
import datetime as _dt
import difflib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from . import core as pk
from .core import PlotkitError

HERE = Path(__file__).parent

# =================================================================== vocabulary
KINDS = ("bar", "hbar", "line", "scatter", "histogram", "heatmap", "pie")
KIND_ALIASES = {"막대": "bar", "막대그래프": "bar", "column": "bar", "columns": "bar", "bars": "bar",
                "grouped_bar": "bar", "stacked_bar": "bar", "barh": "hbar", "horizontal_bar": "hbar",
                "가로막대": "hbar", "가로 막대": "hbar", "선": "line", "꺾은선": "line", "lines": "line",
                "trend": "line", "timeseries": "line", "time_series": "line", "산점도": "scatter",
                "점": "scatter", "points": "scatter", "dots": "scatter", "dot": "scatter", "히스토그램": "histogram",
                "hist": "histogram", "분포": "histogram", "distribution": "histogram", "히트맵": "heatmap",
                "heat": "heatmap", "heat_map": "heatmap", "matrix": "heatmap", "원": "pie", "원그래프": "pie",
                "파이": "pie", "donut": "pie", "doughnut": "pie"}
AGGS = ("mean", "sum", "count", "median", "min", "max", "std", "first", "last", "nunique")
AGG_ALIASES = {"평균": "mean", "avg": "mean", "average": "mean", "합": "sum", "합계": "sum", "total": "sum",
               "개수": "count", "건수": "count", "횟수": "count", "n": "count", "size": "count",
               "중앙값": "median", "최대": "max", "최댓값": "max", "최소": "min", "최솟값": "min",
               "표준편차": "std", "stdev": "std", "sd": "std", "고유": "nunique", "distinct": "nunique"}
PERIODS = {"day": "D", "일": "D", "daily": "D", "week": "W-MON", "주": "W-MON", "weekly": "W-MON",
           "month": "MS", "월": "MS", "monthly": "MS", "quarter": "QS", "분기": "QS", "year": "YS", "연": "YS"}
PERIOD_NAMES = ("day", "week", "month", "quarter", "year")          # the canonical names; the rest of PERIODS are aliases
PALETTE = pk.COMBINE_COLORS
GRAYS = ["#222222", "#777777", "#aaaaaa", "#444444", "#cccccc", "#999999", "#555555", "#bbbbbb"]
HIGHLIGHT_GRAY = "#c8c8c8"

AXIS_KEYS = {"col", "label", "min", "max", "step", "log", "flip", "rotate", "format", "agg", "period",
             "order", "bins", "label_size", "tick_size", "date_format", "_names"}
# chart axes: plotkit.core.AXIS_ALIASES first, then these (so "reverse" -> "invert" -> "flip")
AXIS_EXTRA_ALIASES = {**dict.fromkeys(("aggregate", "aggregation", "function", "func", "집계", "stat"), "agg"),
                      **dict.fromkeys(("group", "freq", "resample", "주기", "단위"), "period"),
                      **dict.fromkeys(("invert", "reverse", "reversed", "inverse", "뒤집기"), "flip"),
                      **dict.fromkeys(("bin", "구간"), "bins"),
                      **dict.fromkeys(("categories", "category_order", "순서"), "order"),
                      **dict.fromkeys(("tick_format", "number_format", "fmt"), "format"),
                      **dict.fromkeys(("rotation", "angle", "회전"), "rotate")}
TOP_KEYS = {"file", "sheets", "read", "chart", "x", "y", "by", "z", "filter", "stack", "sort", "top", "smooth",
            "values", "colors", "highlight", "ref", "trend", "corr", "bins", "density", "error", "percent",
            "title", "legend", "size", "dpi", "font", "font_size", "text_color", "grid", "output", "data_code",
            "code", "echarts", "asks", "point_size", "alpha", "orient", "cmap", "engine", "notes"}
TOP_ALIASES = {"type": "chart", "kind": "chart", "plot": "chart", "chart_type": "chart", "그래프": "chart",
               "sheet": "sheets", "files": "file", "path": "file", "group": "by", "group_by": "by",
               "groupby": "by", "color_by": "by", "hue": "by", "series": "by", "split": "by", "색 구분": "by",
               "where": "filter", "filters": "filter", "조건": "filter", "query": "filter",
               "stacked": "stack", "누적": "stack", "order": "sort", "정렬": "sort", "limit": "top", "상위": "top",
               "moving_average": "smooth", "rolling": "smooth", "이동평균": "smooth", "labels": "values",
               "value_labels": "values", "show_values": "values", "값 표시": "values", "palette": "colors",
               "color": "colors", "색": "colors", "강조": "highlight", "lines": "ref", "reference": "ref",
               "refs": "ref", "기준선": "ref", "fit": "trend", "regression": "trend", "추세선": "trend",
               "correlation": "corr", "상관": "corr", "bin": "bins", "구간": "bins", "errorbar": "error",
               "error_bar": "error", "errors": "error", "에러바": "error", "figsize": "size", "그림 크기": "size",
               "fontsize": "font_size", "글자 크기": "font_size", "제목": "title", "범례": "legend", "격자": "grid",
               "format": "output.format", "transform": "data_code", "python_data": "data_code",
               "extra_code": "code", "echarts_patch": "echarts", "marker_size": "point_size",
               "opacity": "alpha", "orientation": "orient", "colormap": "cmap", "colorscale": "cmap",
               "x축": "x", "y축": "y", "values_col": "z", "value": "z", "color_scale": "cmap"}
CHART_KEYS = frozenset({"chart"} | {k for k, v in TOP_ALIASES.items() if v == "chart"})   # type, kind, plot, 그래프 ...


def is_chart_spec(user):
    """True when the spec names a chart under "chart" or any of its aliases (the router sends it here)."""
    return isinstance(user, dict) and any(k in CHART_KEYS or str(k).lower() in CHART_KEYS for k in user)


SCHEMA_DOC = {
    "chart": '"bar" | "hbar" | "line" | "scatter" | "histogram" | "heatmap" | "pie"',
    "file / sheets / read": "as in plotkit; with several sheets or files the rows are stacked and a column "
                            "\"sheet\" / \"file\" says where each row came from (default: the first sheet)",
    "x / y": 'a column (name, part of a name, or letter) or {"col", "label", "min", "max", "step", "log", "flip", '
             '"rotate", "format", "order", "period", "bins", "date_format"}; y may be a list of columns (one series each)',
    "y.agg": '"mean" | "sum" | "count" | "median" | "min" | "max" | "std" | "nunique"; bar/line/pie/heatmap '
             'group the rows by x (and by) and aggregate; "y": "count" counts rows',
    "x.period": 'date x: "day" | "week" | "month" | "quarter" | "year" groups dates',
    "by": "column that splits the data into series (one colour each); grouped bars, or stacked with \"stack\": true",
    "z": 'heatmap cell value: a column or {"col", "agg"} (default "count" of rows)',
    "filter": 'list of conditions: "반응기 == R3", "주차 >= 10", "촉매 로트 in [FC-2405, FC-2407]", '
              '"날짜 between 2024-03-01 and 2024-03-31", "등급 != 불합격", "비고 contains 노즐"',
    "sort / top": '"desc" | "asc" (by value) | "x" (by category) | a list of categories; top: keep the N largest '
                  '(pie: the rest go into "기타")',
    "smooth": 'moving average: N or {"window": N, "raw": true to keep the raw line}',
    "values": "true to write the value on bars / heatmap cells / pie slices, or a format like \"{:.1f}\" "
              '(pie: "percent" (default), "value", "both")',
    "colors": 'list of colours, {"<series or category>": colour}, or "mono" for black and grey',
    "highlight": "a category (or list) drawn in colour, the rest grey",
    "ref": 'reference lines: [{"y": 5.2, "text": "목표"}, {"y": "mean"}, {"x": 10}]; "mean"/"median" use all filtered rows',
    "trend": "scatter: true for a straight-line fit per series ({\"label\": true} also writes the slope and R²)",
    "corr": 'heatmap of correlations: a list of numeric columns, or "all"',
    "bins": "histogram: number of bins, {\"width\": w}, or a list of edges; heatmap: bin a numeric x or y with x.bins",
    "density": "histogram: true for density instead of counts",
    "error": 'bar: error bars from the rows of each bar: "std" | "sem" | "minmax"',
    "orient": '"h" draws bars horizontally (same as chart "hbar")',
    "cmap": 'heatmap colours: "viridis" (default), "Blues", "Reds", "RdBu_r", "gray" ...',
    "point_size / alpha": "scatter marker size (points², default 22) / opacity",
    "title / legend / size / dpi / font / font_size / text_color / grid / output": "as in plotkit; legend where may "
             'also be "outside right" / "outside bottom"',
    "data_code": "Python run in a sandbox BEFORE filtering and drawing, on the pandas DataFrame df (also pd, np); "
                 "change or add columns, e.g. \"df['K'] = df['T'] + 273.15\". Works on both engines.",
    "code": "matplotlib only: Python after drawing (fig, ax, plt, np, data)",
    "echarts": "ECharts only: a partial option merged over the drawn chart",
    "asks": 'what the user asked, one entry per ask: [{"ask": "R3만", "how": "key"}, {"ask": "...", "how": '
            '"data_code" | "code" | "echarts" | "unsupported"}]; unsupported asks are reported to the user',
    "stack": 'bar / hbar / histogram: true stacks the series of "by" instead of setting them side by side',
    "percent": "accepted but not drawn yet: percent-stacked bars have no key (mark such an ask unsupported)",
    "engine": '"matplotlib" | "echarts": used only when the host does not choose the engine',
    "notes": "free text for the model's own notes; not drawn",
}


# =================================================================== spec
def _alias_top(user):
    out = {}
    for k, v in user.items():
        kk = TOP_ALIASES.get(k, TOP_ALIASES.get(str(k).lower(), k))
        if kk == "output.format":
            out.setdefault("output", {})["format"] = v
            continue
        out[kk] = v
    return out


def _as_axis(v, where):
    if v is None:
        return {}
    if isinstance(v, (str, int)) and not isinstance(v, bool):
        return {"col": v}
    if isinstance(v, list):                    # several columns: names, or {"col", "label"} each
        cols = [x.get("col", x.get("column")) if isinstance(x, dict) else x for x in v]
        names = {str(c): x["label"] for c, x in zip(cols, v) if isinstance(x, dict) and x.get("label")}
        return {"col": cols, **({"_names": names} if names else {})}
    if not isinstance(v, dict):
        raise PlotkitError(f'"{where}" must be a column name or a dict', 'e.g. "x": "반응기" or "x": {"col": "B", "label": "..."}')
    d = {}
    for k, val in v.items():
        kk = pk.AXIS_ALIASES.get(k, k)
        kk = AXIS_EXTRA_ALIASES.get(kk, kk)
        if kk not in AXIS_KEYS:
            raise PlotkitError(f'unknown key "{where}.{k}".{pk._suggest(kk, AXIS_KEYS)}',
                               f"allowed keys for {where}: {', '.join(sorted(AXIS_KEYS))}")
        d[kk] = val
    return d


def normalize(user):
    if not isinstance(user, dict):
        raise PlotkitError("the spec must be a JSON object")
    s = _alias_top(copy.deepcopy(user))
    unknown = [k for k in s if k not in TOP_KEYS]
    if unknown:
        k = unknown[0]
        raise PlotkitError(f'unknown key "{k}" for a chart.{pk._suggest(k, TOP_KEYS)}',
                           "chart keys: " + ", ".join(sorted(TOP_KEYS - {"engine", "notes"})))
    kind = str(s.get("chart", "")).strip().lower()
    kind = KIND_ALIASES.get(kind, kind)
    if kind not in KINDS:
        raise PlotkitError(f'unknown chart "{s.get("chart")}"', "use one of: " + ", ".join(KINDS))
    if str(s.get("orient", "")).lower() in ("h", "horizontal", "가로") and kind == "bar":
        kind = "hbar"
    s["chart"] = kind
    f = s.get("file")
    if not f:
        raise PlotkitError('missing "file"', 'add "file": "<data file>"')
    s["file"] = pk.expand_files(f if isinstance(f, list) else [f])
    s.setdefault("sheets", None)
    s["read"] = s.get("read") or {}
    for role in ("x", "y", "z"):
        s[role] = _as_axis(s.get(role), role)
    by = s.get("by")
    if isinstance(by, dict):
        s["by"] = by.get("col") or by.get("column")
        if by.get("order"):
            s["_by_order"] = by["order"]
        if by.get("colors"):
            s["colors"] = by["colors"]
    agg = s["y"].get("agg")
    if agg is not None:
        a = AGG_ALIASES.get(str(agg).lower(), str(agg).lower())
        if a not in AGGS:
            raise PlotkitError(f'unknown y.agg "{agg}"', "use one of: " + ", ".join(AGGS))
        s["y"]["agg"] = a
    if isinstance(s["y"].get("col"), str) and s["y"]["col"].strip().lower() in ("count", "개수", "건수", "n"):
        s["y"] = {**s["y"], "col": None, "agg": "count"}
    if s["z"].get("agg"):
        s["z"]["agg"] = AGG_ALIASES.get(str(s["z"]["agg"]).lower(), str(s["z"]["agg"]).lower())
    if isinstance(s["z"].get("col"), str) and s["z"]["col"].strip().lower() in ("count", "개수", "건수", "n"):
        s["z"] = {"col": None, "agg": "count"}
    filt = s.get("filter") or []
    if isinstance(filt, (str, dict)):
        filt = [filt]
    s["filter"] = filt
    title = s.get("title")
    if title is None or isinstance(title, str):
        s["title"] = {"text": title, "size": None, "color": None}
    lg = s.get("legend")
    if lg is None or isinstance(lg, (str, bool)):
        if lg is False or (isinstance(lg, str) and lg.lower() in ("none", "off", "없음", "숨김")):
            s["legend"] = {"where": "best", "show": False, "size": None, "title": None}
        else:
            s["legend"] = {"where": lg if isinstance(lg, str) else "best", "show": True, "size": None, "title": None}
    else:
        s["legend"] = {"where": lg.get("where", lg.get("position", lg.get("loc", "best"))),
                       "show": lg.get("show", True), "size": lg.get("size"), "title": lg.get("title")}
    s["legend"]["where"] = _legend_where(s["legend"]["where"])
    s["size"] = [float(v) for v in (s.get("size") or [6.4, 4.6])]
    s["dpi"] = int(s.get("dpi") or 300)
    s["font_size"] = float(s.get("font_size") or 11)
    s.setdefault("font", None)
    s["_text_color_set"] = "text_color" in s
    s["text_color"] = pk._color(s.get("text_color") or "black", "text_color")
    out = s.get("output") or {}
    if isinstance(out, str):
        out = {"format": out}
    fmt = out.get("format", "png")
    fmt = fmt if isinstance(fmt, list) else [fmt]
    fmt = [str(x).lower().lstrip(".").replace("jpeg", "jpg").replace("tiff", "tif") for x in fmt]
    for x in fmt:
        if x not in pk.FORMATS:
            raise PlotkitError(f'unknown output format "{x}"', "use png, pdf, svg, jpg or tif")
    s["output"] = {"dir": out.get("dir"), "format": fmt, "name": out.get("name")}
    s["asks"] = s.get("asks") or []
    return s


def _legend_where(w):
    w = str(w or "best").strip().lower()
    w = pk.KOREAN_PLACES.get(w, w)
    if any(t in w for t in ("outside", "바깥", "밖")):
        return "outside bottom" if any(t in w for t in ("bottom", "아래", "below", "하단")) else "outside right"
    if w not in pk.LEGEND_PLACES:
        raise PlotkitError(f'unknown legend position "{w}"',
                           "use " + ", ".join(pk.LEGEND_PLACES) + ', "outside right" or "outside bottom"')
    return w


# =================================================================== reading tables
_DATE_RE = re.compile(r"^\d{4}[-./]\d{1,2}[-./]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2})?)?$")


def _cell_kind(c, decimal):
    if c is None or (isinstance(c, str) and not c.strip()):
        return "empty"
    if isinstance(c, (_dt.datetime, _dt.date)):
        return "date"
    if pk._to_num(c, decimal) is not None:
        return "num"
    if isinstance(c, str) and _DATE_RE.match(c.strip()):
        return "date"
    return "text"


def frame_from_rows(rows, decimal=".", header_row=None, data_start_row=None):
    """Raw rows -> pandas DataFrame with typed columns (number, date or text) and the header found."""
    import pandas as pd
    width = max((len(r) for r in rows), default=0)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    kinds = [[_cell_kind(c, decimal) for c in r] for r in rows]
    filled = [sum(k != "empty" for k in r) for r in kinds]
    if not rows or max(filled, default=0) == 0:
        raise PlotkitError("this sheet is empty")
    look = min(len(rows), 40)
    if header_row:
        h = int(header_row) - 1
    else:
        h = None
        for i in range(look):
            if filled[i] < 2 or any(k in ("num", "date") for k in kinds[i]):
                continue
            nxt = [filled[j] for j in range(i + 1, min(len(rows), i + 12)) if filled[j]]
            if nxt and filled[i] >= 0.6 * max(nxt):
                h = i
                break
    units = None
    if data_start_row:
        ds = int(data_start_row) - 1
    elif h is None:
        ds = next(i for i, n in enumerate(filled) if n)
    else:
        ds = h + 1
        while ds < len(rows) and not filled[ds]:
            ds += 1
        if ds < len(rows) and not any(k == "num" for k in kinds[ds]) and ds + 1 < len(rows) \
                and any(k == "num" for k in kinds[ds + 1]) \
                and all(len(str(c)) <= 14 for c in rows[ds] if c is not None):
            units = ds                              # a units row under the names
            ds += 1
    body = [r for r in rows[ds:] if any(c is not None and str(c).strip() for c in r)]
    cols, names = [], []
    for j in range(width):
        vals = [r[j] for r in body]
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in vals):
            continue
        name = str(rows[h][j]).strip() if h is not None and rows[h][j] is not None else ""
        if units is not None and rows[units][j] is not None and str(rows[units][j]).strip():
            u = str(rows[units][j]).strip().strip("()[]")
            if u and u not in name and u not in ("-", "–", "—"):
                name = f"{name} ({u})" if name else u
        name = name or pk.col_letter(j)
        base, k = name, 2
        while name in names:
            name = f"{base} {k}"
            k += 1
        names.append(name)
        cols.append((j, name, _typed(vals, decimal)))
    if not cols:
        raise PlotkitError("no data columns found")
    df = pd.DataFrame({name: v for _, name, v in cols})
    df.attrs["letters"] = {name: pk.col_letter(j) for j, name, _ in cols}
    df.attrs["header_row"] = h + 1 if h is not None else None
    df.attrs["data_start_row"] = ds + 1
    return df


def _typed(vals, decimal):
    import pandas as pd
    nonempty = [v for v in vals if v is not None and not (isinstance(v, str) and not v.strip())]
    n = max(1, len(nonempty))
    nums = [pk._to_num(v, decimal) for v in nonempty]
    if sum(x is not None for x in nums) >= 0.9 * n:
        return pd.Series([pk._to_num(v, decimal) if v is not None else np.nan for v in vals], dtype=float)
    dates = sum(isinstance(v, (_dt.datetime, _dt.date)) or (isinstance(v, str) and bool(_DATE_RE.match(v.strip())))
                for v in nonempty)
    if dates >= 0.9 * n:
        return pd.to_datetime(pd.Series([v if v is not None else None for v in vals]), errors="coerce")
    return pd.Series([str(v).strip() if v is not None and str(v).strip() else None for v in vals], dtype=object)


def load_frame(spec):
    """The table a chart spec asks for, as one DataFrame (several sheets/files stacked)."""
    import pandas as pd
    frames = []
    ro = spec.get("read") or {}
    many_files = len(spec["file"]) > 1
    for f in spec["file"]:
        tables, decimal = pk.read_tables(f, ro)
        if ro.get("decimal"):
            decimal = ro["decimal"]
        names = list(tables)
        sel = spec.get("sheets")
        chosen = names[:1] if sel in (None, "") else pk._select_sheets(names, sel, f)
        for n in chosen:
            try:
                d = frame_from_rows(tables[n], decimal, ro.get("header_row"), ro.get("data_start_row"))
            except PlotkitError as e:
                raise PlotkitError(f'{Path(f).name} / sheet "{n}": {e.message}', e.hint)
            if len(chosen) > 1:
                d["sheet"] = n
            if many_files:
                d["file"] = Path(f).stem
            frames.append(d)
    letters = frames[0].attrs.get("letters", {})
    df = frames[0] if len(frames) == 1 else pd.concat(frames, ignore_index=True, sort=False)
    df.attrs["letters"] = letters
    return df


def preview(path, sheets="all", read=None, max_values=12):
    """What the model sees of a table file: per sheet, the columns with their type and values."""
    tables, decimal = pk.read_tables(path, read or {})
    out = []
    for n in (list(tables) if sheets in ("all", None) else pk._select_sheets(list(tables), sheets, path)):
        try:
            df = frame_from_rows(tables[n], decimal)
        except PlotkitError as e:
            out.append({"sheet": n, "error": e.message})
            continue
        cols = []
        for c in df.columns:
            s = df[c]
            e = {"col": df.attrs["letters"].get(c), "name": c}
            if s.dtype.kind == "f":
                v = s.dropna()
                e.update(type="number", min=_r(v.min()) if len(v) else None, max=_r(v.max()) if len(v) else None)
                if 0 < v.nunique() <= 8:
                    e["values"] = [_r(x) for x in sorted(v.unique())]
            elif s.dtype.kind == "M":
                v = s.dropna()
                e.update(type="date", min=str(v.min().date()) if len(v) else None, max=str(v.max().date()) if len(v) else None)
            else:
                u = s.dropna().unique().tolist()
                e.update(type="text", n_values=len(u), values=u[:max_values] + (["…"] if len(u) > max_values else []))
            cols.append(e)
        out.append({"sheet": n, "rows": int(len(df)), "header_row": df.attrs.get("header_row"), "columns": cols})
    return {"ok": True, "file": str(path), "sheets": out}


def _r(v):
    v = float(v)
    return int(v) if v.is_integer() else float(f"{v:.6g}")


# =================================================================== columns and filters
def find_col(df, query, where):
    q = str(query).strip()
    if q in df.columns:
        return q
    letters = df.attrs.get("letters", {})
    if re.fullmatch(r"[A-Za-z]{1,2}", q):
        hit = [c for c, l in letters.items() if l == q.upper()]
        if hit:
            return hit[0]
    qn, qb = pk._norm(q), pk._base(q)
    scored = []
    for c in df.columns:
        n, b = pk._norm(c), pk._base(c)
        s = 4 if n == qn else 3 if (qb and b == qb) else 2 if (n.startswith(qn) or (qb and b.startswith(qb))) \
            else 1 if (qn in n or (qb and qb in n)) else 0
        if s:
            scored.append((s, c))
    if not scored:
        m = difflib.get_close_matches(q, [str(c) for c in df.columns], n=2, cutoff=0.4)
        raise PlotkitError(f'{where}: no column matches "{query}"' + (f" (closest: {', '.join(m)})" if m else ""),
                           "columns: " + ", ".join(f'{letters.get(c, "?")} "{c}"' for c in df.columns))
    top = max(s for s, _ in scored)
    best = [c for s, c in scored if s == top]
    if len(best) > 1:
        raise PlotkitError(f'{where}: "{query}" matches several columns: ' + ", ".join(best),
                           "use more of the name, or the column letter")
    return best[0]


_OPS = [" not in ", " between ", " contains ", " in ", ">=", "<=", "!=", "==", ">", "<", "="]


def _parse_value(v, series):
    import pandas as pd
    if isinstance(v, str):
        v = v.strip().strip("'\"")
    if series.dtype.kind == "M":
        return pd.Timestamp(str(v))
    if series.dtype.kind == "f":
        x = pk._to_num(v) if not isinstance(v, (int, float)) else float(v)
        if x is None:
            raise PlotkitError(f'"{v}" is not a number, but that column holds numbers')
        return x
    return str(v)


def _split_list(rhs):
    rhs = rhs.strip()
    if rhs[:1] in "[(" and rhs[-1:] in "])":
        rhs = rhs[1:-1]
    return [p.strip().strip("'\"") for p in re.split(r"\s*,\s*", rhs) if p.strip()]


def apply_filter(df, cond):
    """One condition (string or dict) -> a boolean mask."""
    if isinstance(cond, dict):
        if "col" in cond or "column" in cond:
            col, op, val = cond.get("col", cond.get("column")), cond.get("op", "=="), cond.get("value", cond.get("values"))
            if "min" in cond or "max" in cond:
                m = np.ones(len(df), bool)
                c = find_col(df, col, "filter")
                if cond.get("min") is not None:
                    m &= (df[c] >= _parse_value(cond["min"], df[c])).to_numpy()
                if cond.get("max") is not None:
                    m &= (df[c] <= _parse_value(cond["max"], df[c])).to_numpy()
                return m
            return apply_filter(df, (col, op, val))
        m = np.ones(len(df), bool)
        for k, v in cond.items():
            if isinstance(v, dict):
                m &= apply_filter(df, {"col": k, **v})
            elif isinstance(v, list):
                m &= apply_filter(df, (k, "in", v))
            else:
                m &= apply_filter(df, (k, "==", v))
        return m
    if isinstance(cond, (tuple, list)) and len(cond) == 3:
        col, op, val = cond
    else:
        text = str(cond).strip()
        for op_ in _OPS:
            i = text.lower().find(op_)
            if i > 0:
                col, op, val = text[:i].strip(), op_.strip(), text[i + len(op_):].strip()
                break
        else:
            raise PlotkitError(f'cannot read the filter "{cond}"',
                               'write "<column> <op> <value>", op: == != > >= < <= in, not in, between, contains')
    c = find_col(df, col, "filter")
    s = df[c]
    op = {"=": "==", "is": "==", "eq": "==", "ne": "!=", "gt": ">", "ge": ">=", "lt": "<", "le": "<="}.get(str(op).lower(), str(op).lower())
    if op in ("in", "not in"):
        vals = val if isinstance(val, list) else _split_list(str(val))
        vv = [_parse_value(v, s) for v in vals]
        m = s.isin(vv).to_numpy() if s.dtype.kind != "O" else s.astype(str).isin([str(v) for v in vv]).to_numpy()
        return ~m if op == "not in" else m
    if op == "between":
        if isinstance(val, list):
            lo, hi = val[0], val[1]
        else:
            parts = re.split(r"\s+(?:and|to|~|-|부터|에서)\s+|\s*~\s*|\s*,\s*", str(val).strip().strip("[]()"))
            parts = [p for p in parts if p.strip()]
            if len(parts) != 2:
                raise PlotkitError(f'cannot read the range in "{cond}"', 'write "<column> between A and B"')
            lo, hi = parts
        hi_text = str(hi).strip().strip("'\"")
        lo, hi = _parse_value(lo, s), _parse_value(hi, s)
        if s.dtype.kind == "M" and len(hi_text) <= 10:          # a date alone: the whole day
            import pandas as pd
            hi = hi + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        return ((s >= lo) & (s <= hi)).fillna(False).to_numpy()
    if op == "contains":
        return s.astype(str).str.contains(str(val).strip("'\""), regex=False, na=False).to_numpy()
    v = _parse_value(val, s)
    if s.dtype.kind == "M" and op in ("<=", ">") and len(str(val).strip().strip("'\"")) <= 10:
        import pandas as pd
        v = v + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)    # "<= 2026-08-30" includes that day
    if op == "==":
        return (s.astype(str) == str(v)).to_numpy() if s.dtype.kind == "O" else (s == v).fillna(False).to_numpy()
    if op == "!=":
        return (s.astype(str) != str(v)).to_numpy() if s.dtype.kind == "O" else (s != v).fillna(True).to_numpy()
    if s.dtype.kind == "O":
        raise PlotkitError(f'"{op}" needs a number or date column, and "{c}" holds text', "use == or in")
    return {">": s > v, ">=": s >= v, "<": s < v, "<=": s <= v}[op].fillna(False).to_numpy()


# =================================================================== the data hatch
def run_data_code(df, code, timeout=60):
    """Run the model's data_code on df in the sandbox (sandbox.py); returns the new df."""
    from . import sandbox
    attrs = dict(df.attrs)
    df.attrs = {}
    try:
        out = sandbox.run(code, {"df": df}, ["df"], timeout=timeout,
                          hint="names: df (pandas DataFrame of the table), pd, np; leave the result in df")["df"]
    finally:
        df.attrs = attrs
    import pandas as pd
    if not isinstance(out, pd.DataFrame):
        raise PlotkitError("data_code must leave a DataFrame in df")
    out.attrs = {"letters": {c: l for c, l in attrs.get("letters", {}).items() if c in out.columns}}
    return out


# =================================================================== figure model
def _agg(series, how):
    if how == "count":
        return float(series.size)
    s = series.dropna()
    if how == "nunique":
        return float(s.nunique())
    if not len(s):
        return float("nan")
    if how in ("first", "last"):
        return float(s.iloc[0 if how == "first" else -1])
    return float(getattr(s, how)())


def _natural_key(v):
    if isinstance(v, (int, float, np.integer, np.floating)):
        return (0, float(v), "")
    s = str(v)
    m = re.match(r"^(\D*?)(\d+(?:\.\d+)?)(.*)$", s)
    return (1, float(m.group(2)), m.group(1) + m.group(3)) if m else (2, 0.0, s)


def _cat_label(v):
    import pandas as pd
    if isinstance(v, pd.Timestamp):
        return str(v.date()) if v == v.normalize() else str(v)
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _period_key(s, period):
    p = PERIODS.get(str(period).lower(), None)
    if p is None:
        raise PlotkitError(f'unknown period "{period}"', "use day, week, month, quarter or year")
    if s.dtype.kind != "M":
        raise PlotkitError("x.period needs a date column", "pick the date column as x")
    if p == "W-MON":
        return (s - __import__("pandas").to_timedelta(s.dt.weekday, unit="D")).dt.normalize()
    return s.dt.to_period({"D": "D", "MS": "M", "QS": "Q", "YS": "Y"}[p]).dt.start_time


SOFT = {"red": "#c0392b", "green": "#2e8b57", "blue": "#1f4e9c", "orange": "#e07b1f", "purple": "#7b3fa0",
        "yellow": "#d4ac0d", "gold": "#d4ac0d", "gray": "#8c8c8c", "grey": "#8c8c8c", "brown": "#8c564b", "pink": "#d6609a"}


def _named(c, where):
    """A user's colour, with plain names (red, 초록, ...) drawn in a softer shade of the same hue."""
    col = pk._color(c, where)
    return SOFT.get(str(col).strip().lower(), col)


def _colors_for(spec, names):
    c = spec.get("colors")
    out = {}
    if isinstance(c, str) and c.lower() in ("mono", "흑백", "black and white", "bw", "grayscale", "gray", "grey"):
        return {n: GRAYS[i % len(GRAYS)] for i, n in enumerate(names)}
    if isinstance(c, list):
        for i, n in enumerate(names):
            out[n] = _named(c[i % len(c)], "colors")
        return out
    if isinstance(c, dict):
        lower = {str(k).strip().lower(): v for k, v in c.items()}
        for i, n in enumerate(names):
            v = c.get(n, lower.get(str(n).strip().lower()))
            out[n] = _named(v, f"colors.{n}") if v else PALETTE[i % len(PALETTE)]
        return out
    if isinstance(c, str) and c:
        col = _named(c, "colors")
        return {n: col for n in names}
    return {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(names)}


def _order(values, how, by_value=None):
    vals = list(values)
    if isinstance(how, list):
        want = [str(v) for v in how]
        lab = {_cat_label(v): v for v in vals}
        first = [lab[w] for w in want if w in lab]
        return first + [v for v in vals if v not in first]
    if how in ("desc", "asc", "내림차순", "오름차순", "descending", "ascending") and by_value is not None:
        rev = how in ("desc", "내림차순", "descending")
        return sorted(vals, key=lambda v: (np.nan_to_num(by_value.get(v, np.nan), nan=-np.inf)), reverse=rev)
    return sorted(vals, key=_natural_key)


def build_model(spec, df):
    """The engine-neutral figure: what to draw, with every number already computed."""
    import pandas as pd
    kind = spec["chart"]
    notes = []
    if spec.get("data_code"):
        df = run_data_code(df, spec["data_code"])
    n_rows = len(df)
    mask = np.ones(len(df), bool)
    for cond in spec["filter"]:
        mask &= apply_filter(df, cond)
    df = df[mask].copy()
    if not len(df):
        raise PlotkitError("no rows left after the filters", f"filters: {spec['filter']}; check the values with preview")
    xs, ys = spec["x"], spec["y"]
    model = {"kind": kind, "series": [], "notes": notes, "rows_total": n_rows, "rows_used": int(len(df)),
             "x": {"label": xs.get("label"), "type": "category"}, "y": {"label": ys.get("label"), "type": "value"},
             "refs": []}
    by = find_col(df, spec["by"], "by") if spec.get("by") else None
    if by:
        df = df[df[by].notna() & (df[by].astype(str).str.strip() != "")]
        model["legend_title"] = re.sub(r"\s*[\(\[][^()\[\]]*[\)\]]\s*$", "", str(by))

    if kind == "heatmap":
        return _heatmap_model(spec, df, model)
    if kind == "histogram":
        return _hist_model(spec, df, model, by)

    xcol = find_col(df, xs["col"], "x") if xs.get("col") is not None else None
    ycols = ys.get("col")
    ylist = ycols if isinstance(ycols, list) else ([ycols] if ycols is not None else [])
    ycol_names = [find_col(df, c, "y") for c in ylist]
    agg = ys.get("agg")

    if kind == "pie":
        lab = xcol or by
        if lab is None:
            raise PlotkitError('pie needs the slice labels: "x": "<category column>"')
        how = agg or ("sum" if ycol_names else "count")
        g = df.groupby(df[lab].map(_cat_label), dropna=True)
        vals = g.size().astype(float) if how == "count" else g[ycol_names[0]].agg(lambda s: _agg(s, how))
        vals = vals[vals > 0]
        order = _order(vals.index, spec.get("sort") or "desc", vals.to_dict())
        labels, values = [str(v) for v in order], [float(vals[v]) for v in order]
        top = spec.get("top")
        if top and len(labels) > int(top):
            rest = sum(values[int(top):])
            labels, values = labels[:int(top)] + ["기타"], values[:int(top)] + [rest]
        tot = sum(values)
        model["pie"] = {"labels": labels, "values": values, "shares": [v / tot for v in values],
                        "colors": list(_colors_for(spec, labels).values()), "show": spec.get("values", "percent")}
        model["agg"] = how
        model["value_name"] = ycol_names[0] if ycol_names else "count"
        return model

    if xcol is None:
        raise PlotkitError(f'{kind} needs "x"', "columns: " + ", ".join(df.columns))
    xser = df[xcol]
    if xs.get("period"):
        xser = _period_key(xser, xs["period"])
        model["x"]["period"] = xs["period"]
    elif xs.get("bins") and kind in ("bar", "hbar", "line"):
        xser = _bin_series(xser, xs["bins"])
    is_num_x = xser.dtype.kind in "fiu" and kind in ("line", "scatter")
    is_time_x = xser.dtype.kind == "M"
    model["x"]["type"] = "time" if is_time_x and kind in ("line", "scatter") else ("value" if is_num_x else "category")
    model["x"]["label"] = model["x"]["label"] or xcol
    if kind in ("bar", "hbar") and is_time_x:
        xser = xser.map(_cat_label)

    # series: either several y columns, or one y split by "by"
    if len(ycol_names) > 1 and by:
        raise PlotkitError('use either several y columns or "by", not both')
    hl_want = None
    if kind == "scatter" and spec.get("highlight") is not None:
        hl = spec["highlight"]
        hl_want = [str(h) for h in (hl if isinstance(hl, list) else [hl])]
        if not by:                                 # find the column the highlighted value lives in
            cand = [c for c in df.columns if df[c].dtype.kind == "O" and all((df[c].astype(str) == w).any() for w in hl_want)]
            if len(cand) != 1:
                raise PlotkitError(f'highlight {hl!r}: cannot tell which column it is in', 'add "by": "<column>"')
            df = df.copy()
            df["__hl"] = np.where(df[cand[0]].astype(str).isin(hl_want), df[cand[0]].astype(str), "기타")
            model["legend_title"] = re.sub(r"\s*[\(\[][^()\[\]]*[\)\]]\s*$", "", str(cand[0]))
            by = "__hl"
    if kind == "scatter":
        if not ycol_names:
            raise PlotkitError('scatter needs "y"')
        groups = [(None, df.index)] if not by else [(k, idx) for k, idx in df.groupby(df[by].map(_cat_label)).groups.items()]
        names = [k for k, _ in groups]
        if by:
            names = _order(names, spec.get("_by_order") or "x")
        cmap = _colors_for(spec, names if by else [ycol_names[0]])
        if hl_want:
            given = spec.get("colors") if isinstance(spec.get("colors"), dict) else {}
            cmap = {n: (_named(given[n], "colors") if n in given else PALETTE[1]) if n in hl_want else HIGHLIGHT_GRAY for n in names}
        gidx = dict(groups)
        for k in names:
            idx = gidx[k]
            sx, sy = xser.loc[idx], df.loc[idx, ycol_names[0]]
            ok = sx.notna() & sy.notna()
            model["series"].append({"name": str(k) if by else ycol_names[0], "color": cmap[k if by else ycol_names[0]],
                                    "x": _plain(sx[ok]), "y": sy[ok].astype(float).tolist()})
        model["y"]["label"] = model["y"]["label"] or ycol_names[0]
        model["legend_needed"] = bool(by)
        if spec.get("trend"):
            for s in model["series"]:
                xv = _as_float(s["x"])
                if len(xv) >= 3:
                    a, b = np.polyfit(xv, s["y"], 1)
                    r = np.corrcoef(xv, s["y"])[0, 1]
                    s["trend"] = {"slope": float(a), "intercept": float(b), "r2": float(r * r),
                                  "x": [float(np.min(xv)), float(np.max(xv))]}
            model["trend_label"] = isinstance(spec["trend"], dict) and bool(spec["trend"].get("label"))
        _refs(spec, model, df, ycol_names[0])
        return model

    # bar / hbar / line: aggregate y per x (and per series)
    how = agg or ("count" if not ycol_names else None)
    frame = pd.DataFrame({"__x": xser})
    if by:
        frame["__s"] = df[by].map(_cat_label)
    for c in ycol_names:
        frame[c] = df[c]
    dup = frame.duplicated(subset=["__x"] + (["__s"] if by else [])).any()
    if how is None:
        how = "mean" if dup or kind in ("bar", "hbar") else "first"
        if dup:
            notes.append(f"several rows per {xcol}{' and ' + by if by else ''}: the {'mean' if how == 'mean' else how} is drawn")
    model["agg"] = how
    series_specs = []
    if by:
        for k, sub in frame.groupby("__s"):
            series_specs.append((k, sub, ycol_names[0] if ycol_names else None))
        names = _order([k for k, _, _ in series_specs], spec.get("_by_order") or "x")
        series_specs.sort(key=lambda t: names.index(t[0]))
    elif len(ycol_names) > 1:
        shown = {find_col(df, k, "y"): v for k, v in (ys.get("_names") or {}).items()}
        series_specs = [(shown.get(c, c), frame, c) for c in ycol_names]
    else:
        series_specs = [(ycol_names[0] if ycol_names else "count", frame, ycol_names[0] if ycol_names else None)]
    per = []
    counts_n = {}
    for name, sub, yc in series_specs:
        if not dup and how in ("first", "last", "mean", "sum", "max", "min", "median") and yc is not None:
            vals = sub.set_index("__x")[yc].astype(float)      # one row per x: nothing to aggregate
            counts_n[name] = vals.notna().astype(int)
            g = None
        else:
            g = sub.groupby("__x", sort=False)
            vals = g.size().astype(float) if how == "count" or yc is None else g[yc].agg(lambda s, h=how: _agg(s, h))
            counts_n[name] = g.size()
        err = None
        if spec.get("error") and yc is not None and kind in ("bar", "hbar", "line") and g is not None:
            e = str(spec["error"]).lower()
            if e in ("std", "sd", "표준편차"):
                err = g[yc].std()
            elif e in ("sem", "se", "표준오차"):
                err = g[yc].sem()
            elif e in ("minmax", "range", "min-max"):
                err = (vals - g[yc].min(), g[yc].max() - vals)
            else:
                raise PlotkitError(f'unknown error "{spec["error"]}"', "use std, sem or minmax")
        per.append((name, vals, err))
    allx = []
    for _, vals, _ in per:
        allx += [v for v in vals.index if v not in allx]
    if model["x"]["type"] == "category":
        tot = {}
        for _, vals, _ in per:
            for k, v in vals.items():
                tot[k] = tot.get(k, 0) + (0 if np.isnan(v) else v)
        sort = xs.get("order") or spec.get("sort") or "x"
        allx = _order(allx, sort, tot)
        if spec.get("top"):
            allx = _order(allx, "desc", tot)[:int(spec["top"])] if sort in ("x",) else allx[:int(spec["top"])]
        cats = [_cat_label(v) for v in allx]
        model["x"]["categories"] = cats
    else:
        allx = sorted(allx)
    names = [str(n) for n, _, _ in per]
    hl = spec.get("highlight")
    cmap = _colors_for(spec, names)
    for name, vals, err in per:
        empty = 0.0 if how in ("count", "sum", "nunique") else float("nan")
        y = [float(vals.get(v, np.nan)) if v in vals.index else empty for v in allx]
        s = {"name": str(name), "color": cmap[str(name)], "y": y,
             "n": [int(counts_n[name].get(v, 0)) if v in counts_n[name].index else 0 for v in allx]}
        if model["x"]["type"] != "category":
            s["x"] = _plain(pd.Series(allx))
        if err is not None:
            if isinstance(err, tuple):
                s["err"] = [[float(err[0].get(v, np.nan)) for v in allx], [float(err[1].get(v, np.nan)) for v in allx]]
            else:
                e = [float(err.get(v, np.nan)) for v in allx]
                s["err"] = [e, e]
        model["series"].append(s)
    if hl is not None and kind in ("bar", "hbar"):
        want = {str(h) for h in (hl if isinstance(hl, list) else [hl])}
        base = model["series"][0]["color"] if spec.get("colors") else PALETTE[1]
        for s in model["series"]:
            s["bar_colors"] = [(_colors_for(spec, [c]).get(c, base) if spec.get("colors") else base) if c in want
                               else HIGHLIGHT_GRAY for c in model["x"]["categories"]]
    if spec.get("smooth") and kind == "line":
        w = spec["smooth"]["window"] if isinstance(spec["smooth"], dict) else spec["smooth"]
        keep = isinstance(spec["smooth"], dict) and spec["smooth"].get("raw")
        new = []
        for s in model["series"]:
            sm = pd.Series(s["y"]).rolling(int(w), min_periods=1).mean().tolist()
            if keep:
                new.append({**s, "alpha": 0.35, "width": 1.0, "name": f"{s['name']}"})
                new.append({**s, "y": sm, "name": f"{s['name']} ({int(w)}점 이동평균)"})
            else:
                new.append({**s, "y": sm, "name": s["name"] if len(model["series"]) > 1 else f"{s['name']} ({int(w)}점 이동평균)"})
        model["series"] = new
        model["smooth"] = int(w)
    model["stack"] = bool(spec.get("stack")) and kind in ("bar", "hbar")
    model["legend_needed"] = len(model["series"]) > 1
    units = {pk._unit(c) for c in ycol_names if pk._unit(c)}
    ylab = ycol_names[0] if len(ycol_names) == 1 else ("count" if not ycol_names else
                                                     (" / ".join(ycol_names) if len(ycol_names) == 2 else (f"({units.pop()})" if len(units) == 1 else "")))
    if how not in ("first", "last") and ycol_names:
        ylab = f"{ylab} ({how})" if how != "mean" or dup else ylab
    elif how == "count":
        ylab = "count"
    model["y"]["label"] = model["y"]["label"] or ylab
    vfmt = spec.get("values")
    if vfmt:
        model["value_format"] = vfmt if isinstance(vfmt, str) and "{" in vfmt else None
        model["value_labels"] = True
        model["value_kind"] = {"n": "n", "count": "n", "개수": "n", "건수": "n", "both": "both"}.get(str(vfmt).lower(), "value")
    _refs(spec, model, df, ycol_names[0] if ycol_names else None)
    return model


def _plain(s):
    if s.dtype.kind == "M":
        return [v.isoformat() for v in s]
    if s.dtype.kind in "fiu":
        return [float(v) for v in s]
    return [str(v) for v in s]


def _as_float(xs):
    """Numbers, or dates as days since 1970 (matplotlib's date numbers)."""
    import pandas as pd
    if xs and isinstance(xs[0], str):
        return ((pd.to_datetime(pd.Series(xs)) - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1)).to_numpy(dtype=float)
    return np.asarray(xs, dtype=float)


def _bin_series(s, bins):
    """Bin a numeric column into labels "a–b"; bins are closed on the left, [a, b), like a histogram
    (the last one also holds b), unless bins = {"edges": [...], "closed": "right"}."""
    import pandas as pd
    if s.dtype.kind not in "fiu":
        raise PlotkitError("bins need a numeric column")
    edges = _edges(s.dropna().to_numpy(), bins)
    right = isinstance(bins, dict) and str(bins.get("closed", "left")).lower() == "right"
    if all(float(e).is_integer() for e in edges) and all(b - a == 1 for a, b in zip(edges, edges[1:])) \
            and np.allclose(s.dropna(), np.round(s.dropna())):
        return s.map(lambda v: None if pd.isna(v) or v < edges[0] or v > edges[-1] else str(int(v)))   # week 3 stays "3"
    if right:
        cut = pd.cut(s, edges, include_lowest=True)
    else:
        e = list(edges)
        cut = pd.cut(s.where(s != e[-1], e[-1] - 1e-9 * max(1.0, abs(e[-1]))), e, right=False)
    return cut.map(lambda iv: f"{_fmt_num(iv.left)}–{_fmt_num(iv.right)}" if isinstance(iv, pd.Interval) else None)


def _fmt_num(v):
    return f"{v:.4g}"


def _edges(v, bins):
    v = v[np.isfinite(v)]
    if isinstance(bins, list):
        return [float(b) for b in bins]
    if isinstance(bins, dict) and bins.get("edges") and not (len(bins["edges"]) == 2 and (bins.get("width") or bins.get("step"))):
        return [float(b) for b in bins["edges"]]
    if isinstance(bins, dict):
        if bins.get("edges"):                       # {"width": 1, "edges": [3, 28]}: a range cut every width
            bins = {**bins, "min": bins["edges"][0], "max": bins["edges"][-1]}
        if bins.get("range") and len(bins["range"]) == 2:
            bins = {**bins, "min": bins["range"][0], "max": bins["range"][1]}
        w = float(bins.get("width") or bins.get("step"))
        lo = math.floor(float(bins.get("min", v.min())) / w) * w
        hi = float(bins.get("max", v.max()))
        n = max(1, int(math.ceil((hi - lo) / w - 1e-9)))
        return [lo + i * w for i in range(n + 1)] + ([lo + (n + 1) * w] if lo + n * w < hi else [])
    n = int(bins) if bins not in (None, True, "auto") else min(30, max(5, int(np.ceil(np.log2(max(2, v.size)) + 1))))
    return np.histogram_bin_edges(v, bins=n).tolist()


def _hist_model(spec, df, model, by):
    xs = spec["x"]
    xcol = find_col(df, xs["col"], "x") if xs.get("col") is not None else None
    if xcol is None:
        raise PlotkitError('histogram needs "x": the numeric column to count')
    if df[xcol].dtype.kind not in "fiu":
        raise PlotkitError(f'histogram: "{xcol}" is not numeric', "for counts of a text column use chart bar with y count")
    edges = _edges(df[xcol].dropna().to_numpy(dtype=float), spec.get("bins") or xs.get("bins"))
    groups = [(xcol, df)] if not by else list(df.groupby(df[by].map(_cat_label)))
    names = [str(k) for k, _ in groups]
    if by:
        names = _order(names, spec.get("_by_order") or "x")
        groups.sort(key=lambda t: names.index(str(t[0])))
    cmap = _colors_for(spec, names)
    for k, sub in groups:
        v = sub[xcol].dropna().to_numpy(dtype=float)
        cnt, _ = np.histogram(v, bins=edges, density=bool(spec.get("density")))
        model["series"].append({"name": str(k), "color": cmap[str(k)], "counts": cnt.astype(float).tolist(), "n": int(v.size),
                                "mean": float(v.mean()) if v.size else None})
    model["edges"] = [float(e) for e in edges]
    model["x"] = {"label": xs.get("label") or xcol, "type": "value"}
    model["y"]["label"] = spec["y"].get("label") or ("density" if spec.get("density") else "count")
    model["stack"] = bool(spec.get("stack"))
    model["legend_needed"] = bool(by)
    _refs(spec, model, df, xcol, axis="x")
    return model


def _heatmap_model(spec, df, model):
    import pandas as pd
    cmap_name = spec.get("cmap")
    if spec.get("corr"):
        cols = spec["corr"]
        cols = [c for c in df.columns if df[c].dtype.kind == "f"] if cols in ("all", True, "*") else [find_col(df, c, "corr") for c in cols]
        m = df[cols].corr()
        rows, colsn = list(m.index), list(m.columns)
        model["heat"] = {"rows": [str(r) for r in rows], "cols": [str(c) for c in colsn], "z": m.to_numpy().tolist(),
                         "cmap": cmap_name or "RdBu_r", "vmin": -1.0, "vmax": 1.0, "label": "r",
                         "values": spec.get("values", True)}
        model["x"] = {"label": spec["x"].get("label") or "", "type": "category", "categories": model["heat"]["cols"]}
        model["y"] = {"label": spec["y"].get("label") or "", "type": "category", "categories": model["heat"]["rows"]}
        return model
    xs, ys, zs = spec["x"], spec["y"], spec["z"]
    if xs.get("col") is None or ys.get("col") is None:
        raise PlotkitError('heatmap needs "x" and "y" (two columns), and "z" for the cell value (default: row count)',
                           'or "corr": [columns] for a correlation matrix')
    xc, yc = find_col(df, xs["col"], "x"), find_col(df, ys["col"], "y")
    xk = _period_key(df[xc], xs["period"]) if xs.get("period") else (_bin_series(df[xc], xs["bins"]) if xs.get("bins") else df[xc])
    yk = _period_key(df[yc], ys["period"]) if ys.get("period") else (_bin_series(df[yc], ys["bins"]) if ys.get("bins") else df[yc])
    how = zs.get("agg") or ("mean" if zs.get("col") else "count")
    zc = find_col(df, zs["col"], "z") if zs.get("col") else None
    frame = pd.DataFrame({"__x": xk.map(_cat_label), "__y": yk.map(_cat_label)})
    if zc:
        frame["__z"] = df[zc]
    g = frame.groupby(["__y", "__x"])
    vals = g.size().astype(float) if how == "count" or zc is None else g["__z"].agg(lambda s: _agg(s, how))
    xcats = _order(frame["__x"].dropna().unique(), xs.get("order") or "x")
    ycats = _order(frame["__y"].dropna().unique(), ys.get("order") or "x")
    if xs.get("bins"):
        xcats = [c for c in _bin_order(xk) if c in set(xcats)]
    if ys.get("bins"):
        ycats = [c for c in _bin_order(yk) if c in set(ycats)]
    empty = 0.0 if how in ("count", "sum", "nunique") else np.nan      # nothing counted is 0, an empty mean is blank
    z = [[float(vals.get((r, c), empty)) for c in xcats] for r in ycats]
    model["heat"] = {"rows": [str(r) for r in ycats], "cols": [str(c) for c in xcats], "z": z,
                     "cmap": cmap_name or "viridis", "vmin": None, "vmax": None,
                     "label": zs.get("label") or (f"{zc} ({how})" if zc else "count"), "values": spec.get("values", False)}
    model["agg"] = how
    model["x"] = {"label": xs.get("label") or xc, "type": "category", "categories": model["heat"]["cols"]}
    model["y"] = {"label": ys.get("label") or yc, "type": "category", "categories": model["heat"]["rows"]}
    return model


def _bin_order(s):
    """Bin labels "a–b" in the order of their lower edge."""
    labs = {str(c) for c in s.dropna()}
    return sorted(labs, key=lambda t: float(t.split("–")[0]) if "–" in t[1:] else float(t))


def _refs(spec, model, df, ycol, axis="y"):
    refs = spec.get("ref") or []
    if isinstance(refs, dict):
        refs = [refs]
    for r in refs:
        if not isinstance(r, dict):
            raise PlotkitError('each "ref" is a dict like {"y": 5.2, "text": "목표"} or {"y": "mean"}')
        ax = "x" if "x" in r else "y"
        v = r.get(ax)
        if isinstance(v, str) and v.lower() in ("mean", "평균", "median", "중앙값", "avg", "average"):
            col = ycol if ax == "y" or axis == "x" else ycol
            if col is None:
                raise PlotkitError('"mean" needs a y column')
            fn = "median" if v.lower() in ("median", "중앙값") else "mean"
            val = float(getattr(df[col].dropna(), fn)())
            text = r.get("text") or f"{'평균' if fn == 'mean' else '중앙값'} {val:.3g}"
        else:
            if isinstance(v, str) and model.get(ax, {}).get("type") == "category":
                val = v
            else:
                val = float(v) if not (isinstance(v, str) and model["x"].get("type") == "time") else v
            text = r.get("text")
        if axis == "x" and ax == "y" and model["kind"] == "histogram":
            ax = "x"                               # a histogram's mean line is vertical
        model["refs"].append({"axis": ax, "value": val, "text": text,
                              "color": pk._color(r.get("color") or "#555555", "ref.color"),
                              "style": pk.linestyle_name(r.get("linestyle", r.get("style", "dashed")), "ref.linestyle")})


# =================================================================== layout (shared by both engines)
def _nice(lo, hi, nbins=6):
    """Axis limits on round tick values, and the tick step."""
    from .ticks import tick_values
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return 0.0, 1.0, 0.2
    if hi == lo:
        lo, hi = lo - 1, hi + 1
    t = tick_values(lo, hi, nbins)
    step = float(t[1] - t[0])
    return float(t[0]) if t[0] <= lo + 1e-12 else float(t[0] - step), float(t[-1]) if t[-1] >= hi - 1e-12 else float(t[-1] + step), step


def _box_overlap(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def layout(spec, model):
    """Decisions both renderers follow, so they draw the same thing: value-axis limits and ticks,
    the legend corner for "best", label rotation, and heatmap text colours."""
    kind = model["kind"]
    fs = spec["font_size"]
    pw, ph = spec["size"][0] * 72 * 0.78, spec["size"][1] * 72 * 0.70        # plot area in points (rough)
    lims = {}
    if kind in ("bar", "hbar", "histogram"):
        if kind == "histogram":
            tops = np.zeros(len(model["edges"]) - 1)
            hi = 0.0
            for s in model["series"]:
                c = np.array(s["counts"])
                tops = tops + c if model["stack"] else np.maximum(tops, c)
            hi = float(np.nanmax(tops)) if tops.size else 1.0
            lo = 0.0
        else:
            vals = np.array([s["y"] for s in model["series"]], dtype=float)
            tops = np.nansum(np.clip(vals, 0, None), axis=0) if model["stack"] else np.nanmax(vals, axis=0)
            bots = np.nansum(np.clip(vals, None, 0), axis=0) if model["stack"] else np.nanmin(vals, axis=0)
            for s in model["series"]:
                if s.get("err"):
                    e = np.array(s["err"], dtype=float)
                    tops = np.fmax(tops, np.array(s["y"]) + np.nan_to_num(e[1]))
            hi, lo = float(np.nanmax(tops)), min(0.0, float(np.nanmin(bots)))
            for r in model["refs"]:
                if r["axis"] == "y" and not isinstance(r["value"], str):
                    hi = max(hi, float(r["value"]))
        head = 1.04 + (0.08 if model.get("value_labels") else 0)
        lims["v"] = [lo, hi * head if hi > 0 else hi]
    elif kind in ("line", "scatter"):
        ys = np.concatenate([np.asarray(s["y"], dtype=float) for s in model["series"]] or [np.zeros(1)])
        ys = ys[np.isfinite(ys)]
        if ys.size:
            pad = 0.04 * ((ys.max() - ys.min()) or abs(ys.max()) or 1)
            lims["v"] = [float(ys.min() - pad), float(ys.max() + pad)]
        if kind == "scatter" and model["x"]["type"] == "value":
            xs = np.concatenate([np.asarray(s["x"], dtype=float) for s in model["series"]])
            xs = xs[np.isfinite(xs)]
            if xs.size:
                pad = 0.04 * ((xs.max() - xs.min()) or 1)
                lims["x"] = list(_nice(float(xs.min() - pad), float(xs.max() + pad)))
    # the legend corner for "best": the corner that covers the least of what is drawn
    where = spec["legend"]["where"]
    need = (model.get("legend_needed") or (kind == "scatter" and model.get("trend_label"))) and kind not in ("heatmap", "pie")
    if need and where == "best" and "v" in lims:
        names = [s["name"] for s in model["series"]]
        if kind == "scatter" and model.get("trend_label"):
            names += [f"{n} fit: y = 0.000x + 0.000, R² = 0.00" for n in names]
        lfs = (spec["legend"]["size"] or fs * 0.833)
        bw = (max(_tw(n, lfs) / PT for n in names) + 30) / pw
        bh = (len(names) * lfs * 1.5 + 8) / ph
        for _ in range(4):
            lo, hi = lims["v"]
            boxes, pts = [], []
            def fy(v):
                return (v - lo) / ((hi - lo) or 1)
            if kind in ("bar", "hbar"):
                n = len(model["x"]["categories"])
                k = len(model["series"])
                bottom = np.zeros(n)
                for si, s in enumerate(model["series"]):
                    for i, v in enumerate(s["y"]):
                        if not np.isfinite(v):
                            continue
                        w = 0.8 / n / (1 if model["stack"] else k)
                        x0 = (i + 0.1) / n + (0 if model["stack"] else si * w)
                        b0 = bottom[i] if model["stack"] else 0
                        top = fy(b0 + v) + (0.06 if model.get("value_labels") else 0)
                        box = (x0, fy(min(b0, 0)), x0 + w, top)
                        boxes.append(box if kind == "bar" else (box[1], 1 - box[2], box[3], 1 - box[0]))
                    if model["stack"]:
                        bottom = bottom + np.nan_to_num(np.array(s["y"], dtype=float))
            elif kind == "histogram":
                e = model["edges"]
                span = (e[-1] - e[0]) or 1
                bottom = np.zeros(len(e) - 1)
                for s in model["series"]:
                    for i, c in enumerate(s["counts"]):
                        b0 = bottom[i] if model["stack"] else 0
                        boxes.append(((e[i] - e[0]) / span, 0, (e[i + 1] - e[0]) / span, fy(b0 + c)))
                    if model["stack"]:
                        bottom = bottom + np.array(s["counts"])
            else:
                for s in model["series"]:
                    xv = _as_float(s["x"]) if s.get("x") is not None else np.arange(len(s["y"]), dtype=float)
                    yv = np.asarray(s["y"], dtype=float)
                    ok = np.isfinite(xv) & np.isfinite(yv)
                    xv, yv = xv[ok], yv[ok]
                    if not xv.size:
                        continue
                    if kind == "line" and xv.size < 200:      # points along the segments too
                        t = np.linspace(0, 1, 8)[:-1]
                        xv = np.concatenate([xv[:-1, None] + np.diff(xv)[:, None] * t, xv[-1:, None]], axis=None) if xv.size > 1 else xv
                        yv = np.concatenate([yv[:-1, None] + np.diff(yv)[:, None] * t, yv[-1:, None]], axis=None) if yv.size > 1 else yv
                    x0, x1 = (lims["x"][0], lims["x"][1]) if "x" in lims else (float(np.min(xv)), float(np.max(xv)))
                    pts.append(np.column_stack([(xv - x0) / ((x1 - x0) or 1), fy(yv)]))
                pts = np.concatenate(pts) if pts else np.zeros((0, 2))
            m = 0.02
            corners = {"upper right": (1 - bw - m, 1 - bh - m, 1 - m, 1 - m), "upper left": (m, 1 - bh - m, bw + m, 1 - m),
                       "lower right": (1 - bw - m, m, 1 - m, bh + m), "lower left": (m, m, bw + m, bh + m)}
            cost = {}
            for name_, c in corners.items():
                if boxes:
                    cost[name_] = sum(_box_overlap(c, b) for b in boxes)
                else:
                    cost[name_] = float(((pts[:, 0] >= c[0]) & (pts[:, 0] <= c[2]) & (pts[:, 1] >= c[1]) & (pts[:, 1] <= c[3])).sum())
            best = min(cost, key=lambda k_: (cost[k_], list(corners).index(k_)))
            if cost[best] <= 1e-9 or kind not in ("bar", "histogram", "line", "scatter") or \
                    (kind in ("line", "scatter") and _ >= 1):
                break
            lims["v"][1 if kind != "hbar" or True else 0] = hi + (hi - lo) * 0.18     # make room above and try again
        model["legend_where"] = best
    else:
        model["legend_where"] = where
    for k_ in ("v",):
        if k_ in lims:
            lo, hi = lims[k_]
            if kind in ("bar", "hbar", "histogram") and lo >= 0:
                lo = 0.0
            lims[k_] = list(_nice(lo, hi))
    scale = fs / 11
    n_pts = sum(len(s_["y"]) for s_ in model["series"]) if kind == "scatter" else 0
    model["point_size"] = float(spec.get("point_size") or ((9 if n_pts > 300 else 22) * scale ** 2))
    model["point_alpha"] = float(spec.get("alpha") or (0.55 if n_pts > 300 else 0.9))
    if kind == "line":
        dense = max((len(s_["y"]) for s_ in model["series"]), default=0) > 500
        for s_ in model["series"]:
            s_.setdefault("width", 1.0 if dense else 1.8)
        if model["x"]["type"] in ("value", "time"):          # a trend runs edge to edge
            xs = [x for s_ in model["series"] for x in (s_.get("x") or [])]
            if xs:
                xv = _as_float(xs) if model["x"]["type"] == "time" else np.asarray(xs, dtype=float)
                lims["x_tight"] = [float(np.nanmin(xv)), float(np.nanmax(xv))]
    model["lims"] = lims
    model["ticks"] = {}
    from .ticks import tick_values
    for k_ in ("v", "x"):
        if k_ in lims:                                    # limits on round values: ticks every step between them
            lo_, hi_, st_ = lims[k_]
            model["ticks"][k_] = [float(round(v, 10)) for v in np.arange(lo_, hi_ + st_ / 2, st_)]
        elif k_ == "x" and "x_tight" in lims and model["x"]["type"] == "value":
            lo_, hi_ = lims["x_tight"]
            model["ticks"]["x"] = [float(v) for v in tick_values(lo_, hi_, 6)
                                   if lo_ - 1e-9 <= v <= hi_ + 1e-9]
    if kind == "histogram":
        e = model["edges"]
        model["ticks"]["x"] = [float(v) for v in tick_values(e[0], e[-1], 6) if e[0] - 1e-9 <= v <= e[-1] + 1e-9]
    # category labels: rotate when they do not fit side by side
    cats = model["x"].get("categories") or []
    rot = spec["x"].get("rotate")
    if rot is None and cats and kind in ("bar", "line", "heatmap"):
        tick = fs * 0.9
        need_w = sum(_tw(c, tick) / PT + tick * 0.8 for c in cats)
        room = pw * (0.72 if kind == "heatmap" else 0.98)          # a heatmap gives width to its colour bar
        rot = (90 if need_w > 2.2 * room else 45) if need_w > room else 0
    model["rotate_x"] = float(rot or 0)
    if kind == "heatmap":
        from .colors import colormap, colormap_names
        h = model["heat"]
        z = np.array(h["z"], dtype=float)
        fin = z[np.isfinite(z)]
        vmin = h["vmin"] if h["vmin"] is not None else (float(fin.min()) if fin.size else 0)
        vmax = h["vmax"] if h["vmax"] is not None else (float(fin.max()) if fin.size else 1)
        try:
            cm = colormap(h["cmap"])
        except KeyError:
            raise PlotkitError(f'unknown cmap "{h["cmap"]}"', "use one of: " + ", ".join(
                n for n in colormap_names() if not n.endswith("_r")) + ' (add "_r" to reverse)')
        tcol = []
        for row in z:
            out = []
            for v in row:
                if not np.isfinite(v):
                    out.append(None)
                    continue
                out.append("#ffffff" if cm.dark((v - vmin) / ((vmax - vmin) or 1)) else "#000000")
            tcol.append(out)
        h["text_colors"] = tcol
        h["vmin_used"], h["vmax_used"] = vmin, vmax
        h["fill"] = [[None if c is None else cm.hex((v - vmin) / ((vmax - vmin) or 1))
                      for v, c in zip(zr, cr)] for zr, cr in zip(z, tcol)]
    return model


# =================================================================== matplotlib
def draw_mpl(spec, model, out_paths):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import warnings as _w
    _w.filterwarnings("ignore", message="Glyph .* missing")
    texts = [spec["title"].get("text") or "", model["x"].get("label") or "", model["y"].get("label") or ""] + \
            [s["name"] for s in model["series"]] + model["x"].get("categories", []) + \
            (model.get("pie", {}).get("labels") or []) + (model.get("heat", {}).get("rows") or [])
    fspec = {"font": spec["font"], "font_size": spec["font_size"]}
    warn = pk._setup_fonts(fspec, texts)
    tc = spec["text_color"]
    fig, ax = plt.subplots(figsize=tuple(spec["size"]), dpi=spec["dpi"])
    kind = model["kind"]
    lw = 1.8
    if kind in ("bar", "hbar"):
        cats = model["x"]["categories"]
        n = len(model["series"])
        pos = np.arange(len(cats))
        width = 0.8 / (1 if model["stack"] else n)
        bottom = np.zeros(len(cats))
        for i, s in enumerate(model["series"]):
            y = np.array(s["y"], dtype=float)
            off = 0 if model["stack"] or n == 1 else (i - (n - 1) / 2) * width
            colors = s.get("bar_colors") or s["color"]
            err = None
            if s.get("err"):
                err = np.array(s["err"], dtype=float)
            if kind == "bar":
                bars = ax.bar(pos + off, np.nan_to_num(y), width, bottom=bottom if model["stack"] else None,
                              color=colors, label=s["name"], yerr=err, capsize=3 if err is not None else 0,
                              edgecolor="black" if spec.get("colors") in ("mono", "흑백") else None, linewidth=0.6)
            else:
                bars = ax.barh(pos + off, np.nan_to_num(y), width, left=bottom if model["stack"] else None,
                               color=colors, label=s["name"], xerr=err, capsize=3 if err is not None else 0)
            if model.get("value_labels"):
                ax.bar_label(bars, labels=_bar_texts(model, s),
                             label_type="center" if model["stack"] else "edge", fontsize=spec["font_size"] * 0.8,
                             padding=2, color=tc)
            if model["stack"]:
                bottom = bottom + np.nan_to_num(y)
        if kind == "bar":
            ax.set_xticks(pos, cats)
        else:
            ax.set_yticks(pos, cats)
            ax.invert_yaxis()
        val_ax, cat_ax = ("y", "x") if kind == "bar" else ("x", "y")
    elif kind == "line":
        xt = model["x"]["type"]
        for s in model["series"]:
            xv = _mpl_x(s.get("x"), model) if xt != "category" else np.arange(len(model["x"]["categories"]))
            ax.plot(xv, s["y"], color=s["color"], lw=s.get("width", lw), alpha=s.get("alpha", 1.0), label=s["name"],
                    marker="o" if len(s["y"]) <= 30 else None, ms=3.5)
            if s.get("err"):
                e = np.array(s["err"], dtype=float)
                ax.fill_between(xv, np.array(s["y"]) - e[0], np.array(s["y"]) + e[1], color=s["color"], alpha=0.15, lw=0)
        if xt == "category":
            ax.set_xticks(np.arange(len(model["x"]["categories"])), model["x"]["categories"])
        if xt == "time":
            import matplotlib.dates as mdates
            loc = mdates.AutoDateLocator()
            ax.xaxis.set_major_locator(loc)
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
        if "x_tight" in model["lims"]:
            ax.set_xlim(*model["lims"]["x_tight"])
        val_ax, cat_ax = "y", "x"
    elif kind == "scatter":
        ps, al = model["point_size"], model["point_alpha"]
        for s in model["series"]:
            xv = _mpl_x(s["x"], model)
            ax.scatter(xv, s["y"], s=ps, color=s["color"], alpha=al, label=s["name"], edgecolors="none")
            t = s.get("trend")
            if t:
                tx = np.array(t["x"])
                lab = f"{s['name']} fit: y = {t['slope']:.3g}x + {t['intercept']:.3g}, R² = {t['r2']:.2f}" \
                    if model.get("trend_label") else None
                ax.plot(_mpl_x(_from_days(tx, model), model) if model["x"]["type"] == "time" else tx,
                        t["slope"] * tx + t["intercept"], color=s["color"], lw=1.4, ls="--", label=lab)
        if model["x"]["type"] == "time":
            import matplotlib.dates as mdates
            loc = mdates.AutoDateLocator()
            ax.xaxis.set_major_locator(loc)
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
        val_ax, cat_ax = "y", "x"
    elif kind == "histogram":
        e = np.array(model["edges"])
        bottom = np.zeros(len(e) - 1)
        many = len(model["series"]) > 1
        for s in model["series"]:
            c = np.array(s["counts"])
            ax.bar(e[:-1], c, width=np.diff(e), align="edge", bottom=bottom if model["stack"] else None,
                   color=s["color"], alpha=0.55 if many and not model["stack"] else 0.9,
                   edgecolor="white", linewidth=0.5, label=s["name"] if many else None)
            if model["stack"]:
                bottom = bottom + c
        val_ax, cat_ax = "y", "x"
    elif kind == "heatmap":
        h = model["heat"]
        z = np.array(h["z"], dtype=float)
        im = ax.pcolormesh(np.ma.masked_invalid(z), cmap=h["cmap"], vmin=h["vmin"], vmax=h["vmax"],
                           edgecolors="white", linewidth=0.3)          # vector cells in PDF and SVG
        ax.set_xticks(np.arange(len(h["cols"])) + 0.5, h["cols"])
        ax.set_yticks(np.arange(len(h["rows"])) + 0.5, h["rows"])
        ax.invert_yaxis()                                              # the first row on top
        ax.tick_params(length=0)
        cb = fig.colorbar(im, ax=ax)
        cb.solids.set_rasterized(False)                  # keep the colour bar vector in PDF/SVG too
        cb.set_label(h["label"], color=tc)
        if h["values"]:
            fmt = h["values"] if isinstance(h["values"], str) and "{" in h["values"] else _auto_fmt(z[np.isfinite(z)])
            for i in range(z.shape[0]):
                for j in range(z.shape[1]):
                    if np.isfinite(z[i, j]):
                        ax.text(j + 0.5, i + 0.5, fmt.format(z[i, j]), ha="center", va="center",
                                fontsize=spec["font_size"] * 0.75, color=h["text_colors"][i][j])
        val_ax, cat_ax = None, "x"
    elif kind == "pie":
        p = model["pie"]
        show = p["show"]
        def autopct(pct):
            v = pct * sum(p["values"]) / 100
            if show in ("value", "값"):
                return f"{v:.4g}"
            if show in ("both", "둘다"):
                return f"{v:.4g}\n({pct:.1f}%)"
            return f"{pct:.1f}%" if show not in (False, "none") else ""
        wedges, _, autot = ax.pie(p["values"], labels=p["labels"], colors=p["colors"], autopct=autopct,
                                  startangle=90, counterclock=False, pctdistance=0.72,
                                  wedgeprops={"edgecolor": "white", "linewidth": 1},
                                  textprops={"color": tc, "fontsize": spec["font_size"] * 0.9})
        from matplotlib.colors import to_rgb
        for t, wcol in zip(autot, p["colors"]):
            t.set_fontsize(spec["font_size"] * 0.8)
            r_, g_, b_ = to_rgb(wcol)
            t.set_color("white" if 0.299 * r_ + 0.587 * g_ + 0.114 * b_ < 0.55 else "black")    # readable on the slice
        ax.axis("equal")
        val_ax = cat_ax = None
    # axes text and ranges
    if kind != "pie":
        xl = model["x"].get("label") or ""
        yl = model["y"].get("label") or ""
        if kind == "hbar":
            xl, yl = yl, xl
        ax.set_xlabel(xl, color=tc)
        ax.set_ylabel(yl, color=tc)
        ax.tick_params(colors=tc, labelcolor=tc)
        from matplotlib.ticker import MultipleLocator
        lim = model["lims"]
        if "v" in lim:
            lo, hi, step = lim["v"]
            vax = "x" if kind == "hbar" else "y"
            (ax.set_xlim if vax == "x" else ax.set_ylim)(lo, hi)
            (ax.xaxis if vax == "x" else ax.yaxis).set_major_locator(MultipleLocator(step))
        if "x" in lim:
            ax.set_xlim(lim["x"][0], lim["x"][1])
            ax.xaxis.set_major_locator(MultipleLocator(lim["x"][2]))
        elif model["ticks"].get("x") and kind in ("line", "histogram") and model["x"]["type"] == "value" and not spec["x"].get("step"):
            from matplotlib.ticker import FixedLocator
            ax.xaxis.set_major_locator(FixedLocator(model["ticks"]["x"]))
        for role, which in (("x", "x"), ("y", "y")):
            a = spec[role]
            tgt = which if kind != "hbar" else ("y" if which == "x" else "x")
            _mpl_axis_opts(ax, tgt, a, numeric=(tgt == val_ax) or (model[role].get("type") in ("value", "time") and kind not in ("bar", "hbar", "heatmap")),
                           is_value_axis=(tgt == val_ax))
        rot = model["rotate_x"]
        if rot:
            for t in (ax.get_xticklabels()):
                t.set_rotation(float(rot))
                t.set_ha("right" if float(rot) % 90 else "center")
                if float(rot) >= 90:
                    t.set_fontsize(spec["font_size"] * 0.8)
        if spec.get("grid"):
            ax.grid(True, alpha=0.3, axis="y" if kind == "bar" else "x" if kind == "hbar" else "both")
            ax.set_axisbelow(True)
        for r in model["refs"]:
            ls = pk.LINESTYLES.get(r["style"], "--")
            vertical = (r["axis"] == "x") != (kind == "hbar")
            v = r["value"]
            if isinstance(v, str) and model["x"].get("type") == "category":
                v = model["x"]["categories"].index(v) if v in model["x"]["categories"] else None
            elif isinstance(v, str) and model["x"].get("type") == "time":
                v = _mpl_x([v], model)[0]
            if v is None:
                continue
            (ax.axvline if vertical else ax.axhline)(v, color=r["color"], ls=ls, lw=1.2)
            if r["text"]:
                if vertical:
                    ax.annotate(r["text"], xy=(v, 1), xycoords=("data", "axes fraction"), xytext=(3, -3),
                                textcoords="offset points", ha="left", va="top", color=r["color"],
                                fontsize=spec["font_size"] * 0.85)
                else:
                    ax.annotate(r["text"], xy=(1, v), xycoords=("axes fraction", "data"), xytext=(-3, 3),
                                textcoords="offset points", ha="right", va="bottom", color=r["color"],
                                fontsize=spec["font_size"] * 0.85)
    lg = spec["legend"]
    leg = None
    want_legend = model.get("legend_needed") or kind == "scatter" and model.get("trend_label")
    if lg["show"] and want_legend and kind not in ("pie", "heatmap"):
        kw = {"frameon": False, "fontsize": lg["size"] or "small"}
        if lg["title"] or model.get("legend_title"):
            kw["title"] = lg["title"] or model["legend_title"]
            kw["title_fontsize"] = lg["size"] or "small"
        where = model["legend_where"]
        if where == "outside right":
            leg = ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), **kw)
        elif where == "outside bottom":
            leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=min(6, len(model["series"])), **kw)
        else:
            leg = ax.legend(loc=where, **kw)
        for t in leg.get_texts():
            t.set_color(tc)
    elif kind == "pie" and lg["show"] and lg["where"].startswith("outside"):
        leg = ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=lg["size"] or "small")
    title = spec["title"].get("text")
    if title:
        kw = {"color": spec["title"].get("color") or tc}
        if spec["title"].get("size"):
            kw["fontsize"] = spec["title"]["size"]
        ax.set_title(title, **kw)
    fig.tight_layout()
    if spec.get("code"):
        env = {"fig": fig, "ax": ax, "ax1": ax, "plt": plt, "np": np, "data": model}
        try:
            exec(compile(spec["code"], "<spec code>", "exec"), env)
        except Exception as e:  # noqa: BLE001
            plt.close(fig)
            raise PlotkitError(f"the extra code failed: {type(e).__name__}: {e}",
                               'the chart is already drawn from your keys; "code" is only for drawing changes no key covers '
                               '(names: fig, ax, plt, np; data = the drawn numbers, not the table). Remove "code" if the keys '
                               'already do it; to change the data use "data_code"')
        fig.tight_layout()
    if leg is not None and lg["where"].startswith("outside"):
        pk.fit_outside_legend(fig, leg, lg["where"])
    for p in out_paths:
        fig.savefig(p, dpi=spec["dpi"])                 # the asked size exactly, also with the legend outside
    plt.close(fig)
    return warn


def _bar_texts(model, s):
    """The text written on each bar: the value, the row count (n), or both."""
    fmt = model.get("value_format") or _auto_fmt(s["y"])
    kind = model.get("value_kind", "value")
    out = []
    for v, n in zip(s["y"], s.get("n") or [None] * len(s["y"])):
        if not np.isfinite(v):
            out.append("")
        elif kind == "n":
            out.append(f"n={n}")
        elif kind == "both":
            out.append(f"{fmt.format(v)} (n={n})")
        else:
            out.append(fmt.format(v))
    return out


def _auto_fmt(v):
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    if not v.size:
        return "{:g}"
    m = np.nanmax(np.abs(v))
    if np.allclose(v, np.round(v)):
        return "{:.0f}"
    return "{:.0f}" if m >= 100 else "{:.1f}" if m >= 10 else "{:.2f}" if m >= 1 else "{:.3f}"


def _mpl_x(xs, model):
    import pandas as pd
    if xs is None:
        return None
    if model["x"]["type"] == "time":
        return pd.to_datetime(pd.Series(xs)).to_numpy()
    return np.asarray(xs, dtype=float)


def _from_days(d, model):
    import pandas as pd
    return [pd.Timestamp(float(v) * 86400e9).isoformat() for v in d]


def _mpl_axis_opts(ax, which, a, numeric, is_value_axis):
    from matplotlib.ticker import MultipleLocator, StrMethodFormatter
    get = ax.get_xlim if which == "x" else ax.get_ylim
    setl = ax.set_xlim if which == "x" else ax.set_ylim
    if a.get("log") and numeric:
        (ax.set_xscale if which == "x" else ax.set_yscale)("log")
    if numeric:
        lo, hi = get()
        conv = lambda v: float(_as_float([v])[0]) if isinstance(v, str) and not pk._to_num(v) else float(v)  # noqa: E731
        if a.get("min") is not None or a.get("max") is not None:
            setl(conv(a["min"]) if a.get("min") is not None else lo, conv(a["max"]) if a.get("max") is not None else hi)
        if a.get("step"):
            (ax.xaxis if which == "x" else ax.yaxis).set_major_locator(MultipleLocator(float(a["step"])))
        if a.get("format"):
            f = a["format"]
            f = f.replace("{:", "{x:") if "{:" in f else f
            (ax.xaxis if which == "x" else ax.yaxis).set_major_formatter(StrMethodFormatter(f))
    if a.get("flip"):
        (ax.invert_xaxis if which == "x" else ax.invert_yaxis)()
    if a.get("tick_size"):
        ax.tick_params(axis=which, labelsize=a["tick_size"])
    if a.get("label_size"):
        (ax.xaxis if which == "x" else ax.yaxis).label.set_size(a["label_size"])


# =================================================================== ECharts
CMAPS = {"viridis": ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"],
         "blues": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
         "reds": ["#fff5f0", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
         "greens": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
         "rdbu_r": ["#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b"],
         "rdbu": ["#b2182b", "#f4a582", "#f7f7f7", "#92c5de", "#2166ac"],
         "coolwarm": ["#3b4cc0", "#aac7fd", "#dddddd", "#f7b89c", "#b40426"],
         "gray": ["#000000", "#555555", "#999999", "#cccccc", "#ffffff"],
         "greys": ["#ffffff", "#cccccc", "#999999", "#555555", "#000000"],
         "magma": ["#000004", "#51127c", "#b73779", "#fc8961", "#fcfdbf"],
         "inferno": ["#000004", "#56106e", "#bb3754", "#f98e09", "#fcffa4"],
         "plasma": ["#0d0887", "#7e03a8", "#cc4778", "#f89540", "#f0f921"],
         "ylorrd": ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"],
         "cividis": ["#00224e", "#434e6c", "#7d7c78", "#bcaf6f", "#fee838"]}
PT = 96 / 72


def _font_family(spec, texts):
    if spec["font"]:
        return f"{spec['font']}, sans-serif"
    if any(re.search(r"[가-힣ㄱ-ㆎ]", t or "") for t in texts):
        return ("Malgun Gothic, Apple SD Gothic Neo, AppleGothic, NanumGothic, Noto Sans CJK KR, "
                "Noto Sans KR, WenQuanYi Zen Hei, sans-serif")
    return "DejaVu Sans, Arial, Helvetica, sans-serif"


def _echarts_dash(style, width):
    """ECharts lineStyle.type for solid / dashed / dotted / dashdot (dashdot has no keyword: a dash pattern, as in
    plotkit/js/translate.mjs)."""
    return [round(v * max(width, 1), 2) for v in (6.4, 1.6, 1, 1.6)] if style == "dashdot" else style


def _tw(text, size_px):
    """Rough text width in px (CJK counts double)."""
    return sum(2 if ord(ch) > 0x2e80 else 1 for ch in str(text)) * size_px * 0.56


def echarts_option(spec, model, live=False):
    """The figure model as an ECharts option (static export, or live with tooltips and zoom)."""
    kind = model["kind"]
    W, H = spec["size"][0] * 96, spec["size"][1] * 96
    fs = spec["font_size"] * PT
    tc = spec["text_color"]
    texts = [spec["title"].get("text") or "", model["x"].get("label") or "", model["y"].get("label") or ""] + \
            [s["name"] for s in model["series"]] + model["x"].get("categories", []) + \
            (model.get("pie", {}).get("labels") or []) + (model.get("heat", {}).get("rows") or [])
    fam = _font_family(spec, texts)
    ts = {"fontFamily": fam, "color": tc, "fontSize": fs}
    title = spec["title"].get("text")
    opt = {"animation": False, "backgroundColor": "#ffffff", "textStyle": ts, "useUTC": True,
           "title": {"show": bool(title), "text": title or "", "left": "center", "top": 6,
                     "textStyle": {"fontFamily": fam, "color": spec["title"].get("color") or tc,
                                   "fontSize": (spec["title"].get("size") or spec["font_size"] * 1.2) * PT, "fontWeight": "normal"}},
           "series": []}
    lg = spec["legend"]
    show_leg = lg["show"] and (model.get("legend_needed") or (kind == "scatter" and model.get("trend_label"))) and kind not in ("heatmap",)
    if kind == "pie" and lg["show"] and lg["where"].startswith("outside"):
        show_leg = True
    top = 12 + ((spec["title"].get("size") or spec["font_size"] * 1.2) * PT * 1.6 if title else 0)
    grid = {"left": 0, "right": 0, "top": top + 8, "bottom": 0}
    if show_leg:
        names = [s["name"] for s in model["series"]] if kind != "pie" else model["pie"]["labels"]
        lfs = (lg["size"] or spec["font_size"] * 0.833) * PT
        sc = spec["font_size"] / 11
        leg = {"show": True, "data": list(names), "textStyle": {**ts, "fontSize": lfs}, "itemWidth": 18 * sc, "itemHeight": 10 * sc,
               "orient": "vertical"}
        if model.get("legend_title") or lg.get("title"):
            lt = lg.get("title") or model["legend_title"]
            leg["data"] = [{"name": lt, "icon": "none", "textStyle": {**ts, "fontSize": lfs, "fontWeight": "bold"}}] + leg["data"]
            opt["_legend_dummy"] = lt               # a name-only series, added after the data series
            names = [lt] + list(names)
        lw_ = max(_tw(n, lfs) for n in names) + 30
        w = model.get("legend_where") or lg["where"]
        if w == "outside right":
            leg.update(right=8, top="middle")
            grid["right"] += lw_ + 8
        elif w == "outside bottom":
            leg.update(orient="horizontal", left="center", bottom=4)
            grid["bottom"] += lfs * 2.2
        opt["legend"] = leg
        opt["_legend_where"] = w
    if live:
        opt["tooltip"] = {"trigger": "item" if kind in ("pie", "heatmap", "scatter") else "axis", "confine": True}
        if kind in ("line", "scatter"):
            opt["dataZoom"] = [{"type": "inside"}, {"type": "inside", "orient": "vertical"}] if kind == "scatter" else [{"type": "inside"}]
    if kind == "pie":
        p = model["pie"]
        show = p["show"]
        mode = {"value": "value", "값": "value", "both": "both", "둘다": "both"}.get(show, "none" if show in (False, "none") else "percent")
        def ptext(n, v, sh):
            return n if mode == "none" else f"{n}\n{v:.4g}" if mode == "value" else f"{n}\n{v:.4g} ({sh * 100:.1f}%)" if mode == "both" else f"{n}\n{sh * 100:.1f}%"
        r = min(W - grid["right"], H - top) * 0.30
        opt["series"].append({"type": "pie", "radius": [0, r], "center": [W / 2 - (grid["right"] / 2), top + (H - top) / 2],
                              "startAngle": 90, "clockwise": True,
                              "data": [{"name": n, "value": v, "itemStyle": {"color": c}, "label": {"formatter": ptext(n, v, sh)}}
                                       for n, v, c, sh in zip(p["labels"], p["values"], p["colors"], p["shares"])],
                              "label": {"show": True, "color": tc, "fontFamily": fam, "fontSize": fs * 0.9, "overflow": "none"},
                              "labelLine": {"length": 8, "length2": 6},
                              "itemStyle": {"borderColor": "#ffffff", "borderWidth": 1}})
        _place_legend(opt, grid)
        return opt, (W, H)
    # cartesian
    xl, yl = model["x"].get("label") or "", model["y"].get("label") or ""
    cat_axis = {"type": "category", "data": model["x"].get("categories", [])}
    val_axis = {"type": "value", "scale": False}
    if kind == "heatmap":
        h = model["heat"]
        xa = {"type": "category", "data": h["cols"], "name": xl, "splitArea": {"show": False}}
        ya = {"type": "category", "data": h["rows"], "name": yl}
        z = np.array(h["z"], dtype=float)
        fin = z[np.isfinite(z)]
        vmin, vmax = h["vmin_used"], h["vmax_used"]
        from .colors import colormap
        mc = colormap(h["cmap"])
        cm = [mc.hex(t) for t in np.linspace(0, 1, 11)]
        fmt = h["values"] if isinstance(h["values"], str) and "{" in h["values"] else _auto_fmt(fin)
        data = [{"value": [j, i, None if not np.isfinite(z[i, j]) else float(z[i, j])],
                 "label": {"color": h["text_colors"][i][j] or tc,
                           **({"show": True, "formatter": fmt.format(z[i, j])} if h["values"] and np.isfinite(z[i, j]) else {"show": False})}}
                for i in range(z.shape[0]) for j in range(z.shape[1])]
        opt["visualMap"] = {"show": False, "min": vmin, "max": vmax, "inRange": {"color": cm}}
        from .ticks import tick_values
        cticks = [float(t) for t in tick_values(vmin, vmax, 4) if vmin - 1e-9 <= t <= vmax + 1e-9]
        cdec = max((len(f"{t:.10g}".split(".")[1]) if "." in f"{t:.10g}" else 0) for t in cticks) if cticks else 0
        ctxt = [f"{t:.{min(cdec, 4)}f}" for t in cticks]
        cw = max([_tw(t, fs * 0.85) for t in ctxt] or [0])
        grid["right"] += 16 + 12 + 6 + cw + 8 + fs * 1.3
        opt["series"].append({"type": "heatmap", "name": h["label"], "data": data,
                              "label": {"show": bool(h["values"]), "fontSize": fs * 0.75, "fontFamily": fam},
                              "itemStyle": {"borderColor": "#ffffff", "borderWidth": 0.5}})
        _axis_style(xa, spec["x"], ts, fs, xl, horizontal=True)
        _axis_style(ya, spec["y"], ts, fs, yl, horizontal=False)
        xa["axisLabel"]["interval"] = ya["axisLabel"]["interval"] = 0
        if model["rotate_x"]:
            xa["axisLabel"]["rotate"] = model["rotate_x"]
        ya["inverse"] = True
        if spec["y"].get("flip"):
            ya["inverse"] = False
        opt["xAxis"], opt["yAxis"] = xa, ya
        _grid_fit(grid, xa, ya, h["cols"], h["rows"], fs, spec)
        opt["grid"] = {**grid, "containLabel": False}
        opt.pop("_legend_where", None)
        g_top, g_bot = grid["top"], H - grid["bottom"]          # the colour bar beside the plot, as in matplotlib
        bx = W - grid["right"] + 16
        els = [{"type": "rect", "shape": {"x": bx, "y": g_top, "width": 12, "height": g_bot - g_top},
                "style": {"fill": {"type": "linear", "x": 0, "y": 1, "x2": 0, "y2": 0,
                                   "colorStops": [{"offset": i / (len(cm) - 1), "color": c} for i, c in enumerate(cm)]},
                          "stroke": "#333333", "lineWidth": 0.6}}]
        for t, lab in zip(cticks, ctxt):
            y = g_bot - (t - vmin) / ((vmax - vmin) or 1) * (g_bot - g_top)
            els.append({"type": "line", "shape": {"x1": bx + 12, "y1": y, "x2": bx + 16, "y2": y}, "style": {"stroke": "#333333", "lineWidth": 0.8}})
            els.append({"type": "text", "x": bx + 19, "y": y, "style": {"text": lab, "fill": tc, "fontSize": fs * 0.85, "fontFamily": fam,
                                                                       "verticalAlign": "middle"}})
        els.append({"type": "text", "x": bx + 22 + cw + fs * 0.9, "y": (g_top + g_bot) / 2, "rotation": -math.pi / 2,
                    "style": {"text": h["label"], "fill": tc, "fontSize": fs * 0.9, "fontFamily": fam, "align": "center",
                              "verticalAlign": "middle"}})
        opt["graphic"] = [{"type": "group", "children": els}]
        return opt, (W, H)
    if kind in ("bar", "hbar"):
        ca = dict(cat_axis)
        va = dict(val_axis)
        if kind == "bar":
            xa, ya = ca, va
        else:
            xa, ya = va, ca
            ca["inverse"] = True
        for s in model["series"]:
            data = []
            texts = _bar_texts(model, s) if model.get("value_labels") else None
            for k, v in enumerate(s["y"]):
                d = {"value": None if not np.isfinite(v) else v}
                if s.get("bar_colors"):
                    d["itemStyle"] = {"color": s["bar_colors"][k]}
                if texts:
                    d["label"] = {"show": bool(texts[k]), "formatter": texts[k]}
                data.append(d)
            ser = {"type": "bar", "name": s["name"], "data": data, "itemStyle": {"color": s["color"]},
                   "barGap": "0%", "barCategoryGap": "20%"}
            if model["stack"]:
                ser["stack"] = "total"
            if model.get("value_labels"):
                ser["label"] = {"show": True, "position": "inside" if model["stack"] else ("top" if kind == "bar" else "right"),
                                "fontSize": fs * 0.8, "fontFamily": fam, "color": tc}
            opt["series"].append(ser)
            if s.get("err"):
                e = np.array(s["err"], dtype=float)
                opt["series"].append({"type": "custom", "name": s["name"] + " err", "renderItem": "__errorbar__" + (":h" if kind == "hbar" else ""),
                                      "data": [[k, s["y"][k] - e[0][k], s["y"][k] + e[1][k]] for k in range(len(s["y"]))
                                               if np.isfinite(s["y"][k]) and np.isfinite(e[0][k])],
                                      "silent": True, "z": 10})
    elif kind == "line":
        xt = model["x"]["type"]
        xa = dict(cat_axis) if xt == "category" else {"type": "time" if xt == "time" else "value", "scale": True}
        ya = dict(val_axis)
        ya["scale"] = True
        for s in model["series"]:
            xs_ = (_as_float(s["x"]) * 86400e3).tolist() if xt == "time" else s.get("x")
            pts = list(zip(xs_, s["y"])) if xt != "category" else s["y"]
            data = [[x_, (None if not np.isfinite(y_) else y_)] for x_, y_ in pts] if xt != "category" else \
                [None if not np.isfinite(v) else v for v in pts]
            opt["series"].append({"type": "line", "name": s["name"], "data": data, "showSymbol": len(s["y"]) <= 30,
                                  "symbolSize": 5 * spec["font_size"] / 11, "lineStyle": {"color": s["color"], "width": s.get("width", 1.8) * PT,
                                                                 "opacity": s.get("alpha", 1.0)},
                                  "itemStyle": {"color": s["color"]}, "connectNulls": False})
    elif kind == "scatter":
        xt = model["x"]["type"]
        xa = {"type": "time" if xt == "time" else "value", "scale": True}
        ya = dict(val_axis)
        ya["scale"] = True
        ps = model["point_size"]
        for s in model["series"]:
            xs_ = (_as_float(s["x"]) * 86400e3).tolist() if xt == "time" else s["x"]
            opt["series"].append({"type": "scatter", "name": s["name"], "data": [[a, b] for a, b in zip(xs_, s["y"])],
                                  "symbolSize": math.sqrt(ps) * PT * 1.1, "itemStyle": {"color": s["color"],
                                                                                         "opacity": model["point_alpha"]}})
            t = s.get("trend")
            if t:
                tx = t["x"]
                xs_ = tx if xt != "time" else [v * 86400e3 for v in tx]
                opt["series"].append({"type": "line", "name": (f"{s['name']} fit: y = {t['slope']:.3g}x + {t['intercept']:.3g}, R² = {t['r2']:.2f}"
                                                               if model.get("trend_label") else s["name"] + " fit"),
                                      "data": [[xs_[0], t["slope"] * tx[0] + t["intercept"]], [xs_[1], t["slope"] * tx[1] + t["intercept"]]],
                                      "showSymbol": False, "lineStyle": {"color": s["color"], "type": "dashed", "width": 1.4 * PT},
                                      "itemStyle": {"color": s["color"]}})
        if model.get("trend_label") and "legend" in opt:
            opt["legend"]["data"] = [x["name"] for x in opt["series"]]
    elif kind == "histogram":
        e = model["edges"]
        xa = {"type": "value", "min": e[0], "max": e[-1], "scale": True}
        ya = dict(val_axis)
        many = len(model["series"]) > 1
        for s in model["series"]:
            data = [[e[k], e[k + 1], c] for k, c in enumerate(s["counts"])]
            opt["series"].append({"type": "custom", "name": s["name"], "renderItem": "__histbar__",
                                  "data": data, "itemStyle": {"color": s["color"],
                                                               "opacity": 0.55 if many and not model["stack"] else 0.9},
                                  "encode": {"x": [0, 1], "y": 2}, "_stack": model["stack"]})
        if model["stack"]:
            acc = np.zeros(len(e) - 1)
            for ser in opt["series"]:
                for k, d in enumerate(ser["data"]):
                    d.append(float(acc[k]))
                    acc[k] += d[2]
    # axes
    xlab, ylab = (xl, yl) if kind != "hbar" else (yl, xl)
    _axis_style(xa, spec["x"] if kind != "hbar" else spec["y"], ts, fs, xlab, horizontal=True)
    _axis_style(ya, spec["y"] if kind != "hbar" else spec["x"], ts, fs, ylab, horizontal=False)
    if kind == "hbar" and spec["x"].get("flip"):
        ya["inverse"] = False
    lim = model["lims"]
    vax, vspec = (xa, spec["y"]) if kind == "hbar" else (ya, spec["y"])
    if "v" in lim:
        lo, hi, step = lim["v"]
        vax.setdefault("min", lo)
        vax.setdefault("max", hi)
        if not vspec.get("step") and vspec.get("min") is None and vspec.get("max") is None and not vspec.get("log"):
            vax["interval"] = step
    if "x" in lim:
        xa.setdefault("min", lim["x"][0])
        xa.setdefault("max", lim["x"][1])
        if not spec["x"].get("step") and spec["x"].get("min") is None and spec["x"].get("max") is None and not spec["x"].get("log"):
            xa["interval"] = lim["x"][2]
    if "x_tight" in lim:
        lo_, hi_ = lim["x_tight"]
        if xa.get("type") == "time":
            xa.setdefault("min", lo_ * 86400e3)
            xa.setdefault("max", hi_ * 86400e3)
        else:
            xa.setdefault("min", lo_)
            xa.setdefault("max", hi_)
    tk = model.get("ticks") or {}
    for a, which, aspec in ((xa, "x", spec["x"] if kind != "hbar" else spec["y"]), (ya, "y", spec["y"] if kind != "hbar" else spec["x"])):
        if a.get("type") == "category":
            a["axisLabel"]["interval"] = 0
            continue
        if a.get("type") == "time":
            span = (lim.get("x_tight") or [0, 0])[1] - (lim.get("x_tight") or [0, 0])[0]
            a["axisLabel"]["formatter"] = "{HH}:{mm}" if span and span < 2 else ("{MM}-{dd}" if span and span < 120 else "{yyyy}-{MM}")
            continue
        is_v = (which == "y") != (kind == "hbar")
        ticks = tk.get("v") if is_v else tk.get("x")
        if ticks and not aspec.get("step") and not aspec.get("log") and aspec.get("min") is None and aspec.get("max") is None:
            a["axisLabel"]["customValues"] = ticks
            a["axisTick"]["customValues"] = ticks
            a.pop("interval", None)
            dec = max(len(f"{t:.10g}".split(".")[1]) if "." in f"{t:.10g}" else 0 for t in ticks)
            a["axisLabel"]["formatter"] = "__fmt__{:." + str(min(dec, 6)) + "f}"
        elif not a["axisLabel"].get("formatter"):
            a["axisLabel"]["formatter"] = "__fmt__{:.10g}"          # 1190, not 1,190
    if model["rotate_x"] and xa.get("type") == "category":
        xa["axisLabel"]["rotate"] = model["rotate_x"]
    opt["xAxis"], opt["yAxis"] = xa, ya
    _grid_fit(grid, xa, ya, xa.get("data") or [], ya.get("data") or [], fs, spec)
    opt["grid"] = {**grid, "containLabel": False}
    _place_legend(opt, grid)
    for r in model["refs"]:
        vertical = (r["axis"] == "x") != (kind == "hbar")
        v = r["value"]
        item = {"xAxis" if vertical else "yAxis": v}
        if r["text"]:
            item["label"] = {"show": True, "formatter": r["text"], "position": "insideEndTop", "color": r["color"],
                             "fontSize": fs * 0.85, "fontFamily": fam}
        else:
            item["label"] = {"show": False}
        tgt = next((x for x in opt["series"] if x["type"] in ("bar", "line", "scatter")), None)
        if tgt is None:
            tgt = {"type": "line", "data": [], "name": "_ref"}
            opt["series"].append(tgt)
        ml = tgt.setdefault("markLine", {"silent": True, "symbol": "none", "data": []})
        ml["data"].append({**item, "lineStyle": {"color": r["color"], "type": _echarts_dash(r["style"], 1.2 * PT),
                                                  "width": 1.2 * PT}})
    if spec.get("grid"):
        (ya if kind != "hbar" else xa).setdefault("splitLine", {})["show"] = True
    if opt.get("_legend_dummy"):
        opt["series"].append({"type": "line", "name": opt.pop("_legend_dummy"), "data": [], "silent": True})
    return opt, (W, H)


def _place_legend(opt, grid):
    """A legend inside the plot goes in the chosen corner of the grid."""
    w = opt.pop("_legend_where", None)
    leg = opt.get("legend")
    if not leg or w is None or w.startswith("outside"):
        return
    vpos = "top" if "upper" in w else "bottom" if "lower" in w else "middle"
    hpos = "left" if "left" in w else "center" if w in ("upper center", "lower center", "center") else "right"
    if vpos == "top":
        leg["top"] = grid["top"] + 6
    elif vpos == "bottom":
        leg["bottom"] = grid["bottom"] + 6
    else:
        leg["top"] = "middle"
    if hpos == "center":
        leg["left"] = "center"
    elif hpos == "left":
        leg["left"] = grid["left"] + 8
    else:
        leg["right"] = grid["right"] + 8


def _axis_style(a, s, ts, fs, label, horizontal):
    a["name"] = label
    a["nameLocation"] = "middle"
    a["nameTextStyle"] = {**ts, "fontSize": (s.get("label_size") or 0) * PT or fs}
    a["axisLabel"] = {**{k: v for k, v in ts.items() if k != "fontSize"}, "fontSize": (s.get("tick_size") or 0) * PT or fs,
                      "hideOverlap": False}
    a["axisLine"] = {"show": True, "onZero": False, "lineStyle": {"color": "#333333"}}
    a["axisTick"] = {"show": True, "inside": True, "alignWithLabel": True}
    a["splitLine"] = {"show": False}
    if a.get("type") in ("value", "time", "log") or a.get("type") is None:
        for k in ("min", "max"):
            if s.get(k) is not None:
                v = s[k]
                if a.get("type") == "time" and isinstance(v, str):
                    v = float(_as_float([v])[0] * 86400e3)        # the data is UTC milliseconds too
                a[k] = v
        if s.get("step"):
            a["interval"] = float(s["step"])
        if s.get("log"):
            a["type"] = "log"
        if s.get("format"):
            a["axisLabel"]["formatter"] = "__fmt__" + s["format"]
    if s.get("flip"):
        a["inverse"] = not a.get("inverse", False)
    if s.get("rotate") is not None and horizontal:
        a["axisLabel"]["rotate"] = float(s["rotate"])


def _grid_fit(grid, xa, ya, xcats, ycats, fs, spec):
    """Margins from estimated label sizes (SSR has no text metrics)."""
    ylab_w = max([_tw(c, fs) for c in ycats] or [_tw("0000.0", fs)])
    if ya.get("type") in ("value", "log"):
        ylab_w = _tw("00000", fs)
    rot = xa.get("axisLabel", {}).get("rotate")
    longest = max([_tw(c, fs) for c in xcats] or [0])
    if rot is None and xcats and sum(_tw(c, fs) + 8 for c in xcats) > (spec["size"][0] * 96 - ylab_w - 80) * 0.95:
        xa["axisLabel"]["rotate"] = 45
        rot = 45
    xlab_h = fs * 1.2 + (longest * math.sin(math.radians(float(rot))) if rot else 0)
    has_yname = bool(ya.get("name"))
    has_xname = bool(xa.get("name"))
    grid["left"] += ylab_w + 14 + (fs * 1.6 if has_yname else 0)
    ya["nameGap"] = ylab_w + 10
    grid["bottom"] += xlab_h + 10 + (fs * 1.6 if has_xname else 0)
    xa["nameGap"] = xlab_h + 8
    grid["right"] += 18
    grid["top"] += 4


def draw_echarts(spec, model, out_paths, dump_path=None):
    opt, (W, H) = echarts_option(spec, model)
    if spec.get("echarts"):
        from .echarts import validate_patch
        patch = validate_patch(spec["echarts"])
        for k in ("xAxis", "yAxis"):                 # one axis each here; the patch may give a list
            if isinstance(patch.get(k), list):
                patch[k] = patch[k][0] if patch[k] else {}
        opt = _merge(opt, patch)
    fig = {"name": Path(out_paths[0]).stem, "option": opt, "width": W, "height": H, "dpi": spec["dpi"], "size_in": spec["size"],
           "formats": [Path(p).suffix.lstrip(".") for p in out_paths]}
    payload = json.dumps({"out_dir": str(Path(out_paths[0]).parent), "figures": [fig]}, ensure_ascii=False)
    from .echarts import _node
    env = dict(os.environ)
    if dump_path:
        env["PLOTKIT_DUMP_OPTION"] = str(dump_path)
    p = subprocess.run([_node(), str(HERE / "js" / "render_chart.mjs")], input=payload.encode("utf-8"),
                       capture_output=True, timeout=180, env=env)
    out = p.stdout.decode("utf-8", "replace").strip()
    try:
        reply = json.loads(out.splitlines()[-1]) if out else None
    except json.JSONDecodeError:
        reply = None
    if not reply or not reply.get("ok"):
        err = (reply or {}).get("error") or (p.stderr.decode("utf-8", "replace").strip().splitlines() or ["?"])[-1]
        raise PlotkitError(f"the ECharts renderer failed: {err}", "check the echarts patch, or report this")
    return None


def _merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _merge(a.get(k), v) if k in a else v
        return out
    if isinstance(a, list) and isinstance(b, list):
        return [_merge(a[i], b[i]) if i < len(b) else a[i] for i in range(len(a))] + b[len(a):]
    return b


def live_result(user_spec):
    """The chart as an ECharts option for a live chart in the browser (tooltip, zoom; labels belong to the data), in
    the shared result shape (see plotkit.core.plot) with "options" and nothing saved. Number formats and custom
    series are left as "__fmt__..." / "__histbar__" / "__errorbar__" markers: the page revives them with
    plotkit/js/revive.mjs."""
    spec = normalize(user_spec)
    if spec.get("code"):
        raise PlotkitError('"code" only works with the matplotlib engine',
                           'use "data_code" for data changes (both engines), or an "echarts" patch for drawing changes')
    model = layout(spec, build_model(spec, load_frame(spec)))
    opt, _ = echarts_option(spec, model, live=True)
    if spec.get("echarts"):
        from .echarts import validate_patch
        patch = validate_patch(spec["echarts"])
        for k in ("xAxis", "yAxis"):
            if isinstance(patch.get(k), list):
                patch[k] = patch[k][0] if patch[k] else {}
        opt = _merge(opt, patch)
    return {"ok": True, "kind": "chart", "engine": "echarts", "options": [opt], "saved": [],
            "warnings": list(model["notes"]), "not_done": pk.not_done(spec), "values": summary_values(model),
            "chart": model["kind"], "rows_used": model["rows_used"], "rows_total": model["rows_total"]}


def live_options(user_spec):
    """The chart's live ECharts options (a list of one; see live_result)."""
    return live_result(user_spec)["options"]


def curve_as_chart(user):
    """A curve spec (no "chart") whose x column holds dates, e.g. a sensor log: the same plot as a chart line.
    Returns the chart spec, or None when x is not a date column (then plotkit draws the curve as usual)."""
    try:
        x = user.get("x")
        xcol = x.get("col") if isinstance(x, dict) else x
        if not xcol:
            return None
        files = pk.expand_files(user["file"] if isinstance(user["file"], list) else [user["file"]])
        df = load_frame({"file": files, "sheets": user.get("sheets") if user.get("sheets") not in ("all",) else None,
                         "read": user.get("read") or {}})
        c = find_col(df, xcol, "x")
        if df[c].dtype.kind != "M":
            return None
    except Exception:  # noqa: BLE001 - not a table this can read: leave it to plotkit
        return None
    ys = []
    for role in ("y1", "y2"):
        v = user.get(role)
        col = v.get("col") if isinstance(v, dict) else (v if isinstance(v, str) else None)
        if col:
            ys.append(col)
    if not ys:
        return None
    out = {"file": user["file"], "chart": "line", "x": {"col": c, **({"label": x["label"]} if isinstance(x, dict) and x.get("label") else {})},
           "y": ys if len(ys) > 1 else ys[0]}
    for k in ("sheets", "read", "title", "legend", "size", "dpi", "font", "font_size", "text_color", "grid", "output", "asks", "filter"):
        if user.get(k) not in (None, "all") or (k == "sheets" and user.get(k) not in (None, "all")):
            out[k] = user[k]
    cols = [user[r].get("color") for r in ("y1", "y2") if isinstance(user.get(r), dict) and user[r].get("color")]
    if cols:
        out["colors"] = cols
    if isinstance(user.get("y1"), dict) and user["y1"].get("label") and len(ys) == 1:
        out["y"] = {"col": ys[0], "label": user["y1"]["label"]}
    return out


# =================================================================== entry
def plot(user_spec, engine=None, dump_path=None, out_dir=None, formats=None):
    """Draw a chart spec. Returns the shared result (see plotkit.core.plot) plus chart, rows_used, rows_total, summary."""
    eng = pk.engine_name(engine or user_spec.get("engine"))
    spec = pk.set_output(normalize(user_spec), out_dir, formats)
    if spec.get("code") and eng == "echarts":
        raise PlotkitError('"code" only works with the matplotlib engine',
                           'use "data_code" for data changes (both engines), or an "echarts" patch for drawing changes')
    if spec.get("echarts") and eng == "matplotlib":
        raise PlotkitError('"echarts" only works with the ECharts engine',
                           'use "data_code" for data changes, or "code" for drawing changes on matplotlib')
    df = load_frame(spec)
    model = layout(spec, build_model(spec, df))
    first = spec["file"][0]
    outdir = Path(spec["output"]["dir"] or (Path(first).with_suffix("").as_posix() + "_plots"))
    outdir.mkdir(parents=True, exist_ok=True)
    name = spec["output"]["name"] or f"{model['kind']}_" + re.sub(r"[^\w가-힣]+", "_",
                                                                   str(spec["y"].get("col") or spec["x"].get("col") or "chart"))[:40]
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("_") or "chart"
    paths = [str(outdir / f"{name}.{f}") for f in spec["output"]["format"]]
    warnings = list(model["notes"])
    if eng == "echarts":
        draw_echarts(spec, model, paths, dump_path=dump_path)
    else:
        w = draw_mpl(spec, model, paths)
        if w:
            warnings.append(w)
    values = summary_values(model)
    not_done = pk.not_done(spec)
    return {"ok": True, "kind": "chart", "engine": eng, "saved": paths, "warnings": warnings, "not_done": not_done,
            "values": values, "chart": model["kind"], "rows_used": model["rows_used"], "rows_total": model["rows_total"],
            "summary": korean_summary(model, values, paths, not_done, warnings)}


def summary_values(model):
    k = model["kind"]
    if k == "pie":
        p = model["pie"]
        return {"slices": {l: round(v, 4) for l, v in zip(p["labels"], p["values"])},
                "shares": {l: round(s, 4) for l, s in zip(p["labels"], p["shares"])}}
    if k == "heatmap":
        h = model["heat"]
        z = np.array(h["z"], dtype=float)
        if not np.isfinite(z).any():
            return {}
        i, j = np.unravel_index(np.nanargmax(z), z.shape)
        return {"rows": h["rows"], "cols": h["cols"], "max": {"row": h["rows"][i], "col": h["cols"][j], "value": round(float(z[i, j]), 4)}}
    if k == "histogram":
        return {"bins": len(model["edges"]) - 1, "series": {s["name"]: {"n": s["n"], "mean": s["mean"]} for s in model["series"]}}
    if k in ("bar", "hbar"):
        return {"categories": model["x"]["categories"],
                "series": {s["name"]: [None if not np.isfinite(v) else round(v, 4) for v in s["y"]] for s in model["series"]}}
    if k == "line":
        return {"series": {s["name"]: {"n": len(s["y"]), "min": _nanr(np.nanmin(s["y"])), "max": _nanr(np.nanmax(s["y"]))}
                           for s in model["series"]}}
    if k == "scatter":
        return {"series": {s["name"]: {"n": len(s["y"]), **({"slope": round(s["trend"]["slope"], 5), "r2": round(s["trend"]["r2"], 4)}
                                                            if s.get("trend") else {})} for s in model["series"]}}
    return {}


def _nanr(v):
    return None if v is None or not np.isfinite(v) else round(float(v), 4)


KIND_KO = {"bar": "막대", "hbar": "가로 막대", "line": "선", "scatter": "산점도", "histogram": "히스토그램",
           "heatmap": "히트맵", "pie": "원"}


def korean_summary(model, values, paths, not_done, warnings):
    """What was drawn, in Korean, from the numbers (no model involved)."""
    k = model["kind"]
    lines = [f"{KIND_KO[k]} 그래프를 저장했습니다: {', '.join(Path(p).name for p in paths)}"]
    lines.append(f"사용한 행: {model['rows_used']} / {model['rows_total']}")
    if k in ("bar", "hbar"):
        cats = model["x"]["categories"]
        for s in model["series"][:4]:
            pairs = [f"{c} {v:.3g}" for c, v in zip(cats, s["y"]) if np.isfinite(v)][:8]
            lines.append(f"{s['name']}: " + ", ".join(pairs) + (" …" if len(cats) > 8 else ""))
    elif k == "pie":
        lines.append(", ".join(f"{l} {s * 100:.1f}%" for l, s in list(values["shares"].items())[:8]))
    elif k == "heatmap" and values:
        m = values["max"]
        lines.append(f"가장 큰 값: {m['row']} / {m['col']} = {m['value']:.4g}")
    elif k == "scatter":
        for n, d in values["series"].items():
            lines.append(f"{n}: {d['n']}점" + (f", 기울기 {d['slope']:.3g}, R² {d['r2']:.2f}" if "slope" in d else ""))
    elif k == "line":
        for n, d in list(values["series"].items())[:6]:
            lines.append(f"{n}: {d['n']}점, {d['min']:.4g} ~ {d['max']:.4g}" if d["min"] is not None else f"{n}: 값 없음")
    elif k == "histogram":
        for n, d in values["series"].items():
            lines.append(f"{n}: {d['n']}개, 평균 {d['mean']:.4g}" if d["mean"] is not None else f"{n}: 값 없음")
    for r in model["refs"]:
        if r["text"]:
            lines.append(f"기준선: {r['text']}")
    if not_done:
        lines.append("처리하지 못한 요청: " + "; ".join(not_done))
    for w in warnings:
        lines.append(f"참고: {w}")
    return "\n".join(lines)


def schema():
    return {"keys": SCHEMA_DOC, "kinds": list(KINDS), "aggs": list(AGGS)}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("preview")
    p1.add_argument("file")
    p1.add_argument("--sheets", default="all")
    p2 = sub.add_parser("plot")
    p2.add_argument("spec", nargs="?")
    p2.add_argument("--json")
    p2.add_argument("--engine")
    sub.add_parser("schema")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "preview":
            out = preview(a.file, a.sheets)
        elif a.cmd == "schema":
            out = schema()
        else:
            spec = json.loads(a.json) if a.json else json.loads(Path(a.spec).read_text(encoding="utf-8"))
            out = plot(spec, engine=a.engine)
    except PlotkitError as e:
        out = {"ok": False, "error": e.message, "hint": e.hint}
    print(pk.dumps(out))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
