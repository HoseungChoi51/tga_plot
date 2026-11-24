#!/usr/bin/env python3
"""JSON Schemas for constrained decoding of plotkit / chartkit specs.

A schema is built for each request from the data the model is shown: the file names, sheet names and column
names become enums, so a constrained model cannot invent a file, sheet or column, cannot write an unknown key and
cannot write broken JSON. Values that plotkit checks anyway (colours, numbers, filter strings) stay loose.

Two profiles:

  full   The spec exactly as AGENT.md / prompts/v2 describe it (shorthands included). Uses anyOf, free-form
         objects ("echarts", "annotate.<name>"). For llama.cpp, vLLM, SGLang (response_format
         json_schema) and any engine with a full JSON-Schema-to-grammar converter.
  flat   The same spec written as a flat list of settings, for engines with tight schema limits (the Anthropic API:
         every object closed, no maxLength, at most 24 optional parameters and 16 anyOf). Converted back with
         flat_to_spec() before plotkit sees it. The model needs FLAT_NOTE appended to its system prompt.

    import spec_schema as ss
    info = ss.data_info(["data/run_log.xlsx"], root="experiments/eval/cnt")   # files, sheets, columns as the model sees them
    schema = ss.build(info, kinds=("curve", "chart"), hatch="code")   # profile="flat" for the Anthropic API
    ss.validate(spec, schema)                                         # [] when the spec fits

    python experiments/spec_schema.py experiments/eval/cnt/data/run_log.xlsx --root experiments/eval/cnt [--flat] [--hatch echarts]   # print a schema
"""
import copy
import glob
import json
import re
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[1]) not in sys.path:      # the library, when run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plotkit as pk  # noqa: E402

KINDS = ("bar", "hbar", "line", "scatter", "histogram", "heatmap", "pie")      # chartkit.KINDS
AGGS = ("mean", "sum", "count", "median", "min", "max", "std", "first", "last", "nunique")
PERIODS = ("day", "week", "month", "quarter", "year")
HOWS = ("key", "data_code", "code", "echarts", "unsupported")
LEGEND = tuple(pk.LEGEND_PLACES)
LINESTYLES = ("solid", "dashed", "dotted", "dashdot")
FORMATS = ("png", "pdf", "svg", "jpg", "tif")
CORNERS = ("upper left", "upper right", "lower left", "lower right")

# String length limits are off: grammar converters turn "maxLength": n into a bounded repetition that can make
# big grammars slow to build, and the Anthropic API rejects them. max_tokens bounds a runaway string instead.
TEXT_MAX = CODE_MAX = None

FLAT_NOTE = """

## Reply format (settings list)
Write the spec as JSON with "file", "chart", "settings" and "asks" instead of nested keys:
- "chart": the chart kind, or "curve" for an instrument curve (a spec with no "chart" key).
- "settings": one entry per setting, with the nested key written as a dotted path:
  {"key": "x.col", "column": "반응기"} for a column (a list of columns: one entry per column, in order);
  {"key": "x.col", "new_column": "수율_kg"} for a column that your data_code makes;
  {"key": "y.agg", "value": "mean"}, {"key": "title.text", "value": "수율"}, {"key": "x.max", "value": 900},
  {"key": "filter", "value": ["반응기 == R3"]}, {"key": "colors", "value": "mono"} for anything else;
  {"sheet": "런로그"} for a sheet (one entry per sheet);
  {"annotate": "residue", "field": "x", "value": 700} for curve labels ("field": "show", "value": false removes one);
  {"ref_axis": "y", "at": "mean", "text": "평균"} for a chart reference line.
- "echarts" (ECharts settings) is written as {"key": "echarts", "value": "<the JSON object as text>"}.
Everything else is as described above."""


# =================================================================== the data the model sees
def _base_name(name):
    """'일자 (yyyy-mm-dd)' -> '일자', 'CNT수율(g/g-cat)' -> 'CNT수율'; the unit may be left out (prompts/v2)."""
    b = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]\s*$", "", str(name)).strip()
    return b if b and b != name else None


def data_info(files, root=None, inspect=False):
    """Files, sheets and columns of the files the model is shown.

    files: as the request names them (patterns like data/raman/*.csv allowed), relative to root.
    inspect=True reads them like plotkit inspect (the TGA harness); else like chartkit.preview (the CNT harness).
    Returns {"files": [names the spec may use], "sheets": [...], "columns": [...], "multi": bool}."""
    root = Path(root) if root else Path(".")
    names, sheets, cols, n_tables = [], [], [], 0
    for f in files:
        names.append(str(f))
        paths = sorted(Path(p) for p in glob.glob(str(root / f))) if any(c in str(f) for c in "*?") else [root / f]
        for p in paths:
            rel = p.relative_to(root).as_posix() if str(p).startswith(str(root)) else str(p)
            if rel not in names:
                names.append(rel)
            if inspect:
                info = pk.inspect_file(str(p))
                tabs = [(s["name"], [(c["col"], c["name"]) for c in s.get("columns", [])]) for s in info.get("sheets", [])]
            else:
                import chartkit
                pv = chartkit.preview(str(p))
                tabs = [(s["sheet"], [(c["col"], c["name"]) for c in s.get("columns", [])]) for s in pv["sheets"]]
            for sheet, cc in tabs:
                n_tables += 1
                if sheet not in sheets:
                    sheets.append(sheet)
                for letter, name in cc:
                    for v in (name, _base_name(name), letter):
                        if v and str(v) not in cols:
                            cols.append(str(v))
    by_dir = {}
    for n in list(names):
        if "*" not in n and "?" not in n:
            by_dir.setdefault((str(Path(n).parent), Path(n).suffix), []).append(n)
    for (d, ext), group in by_dir.items():  # several files of one kind: the pattern the prompt allows
        if len(group) > 1:
            pat = (f"{d}/*{ext}" if d not in ("", ".") else f"*{ext}")
            if pat not in names:
                names.append(pat)
    if n_tables > 1:                    # chartkit stacks several sheets / files and says where each row came from
        cols += [c for c in ("sheet", "file") if c not in cols]
    return {"files": names, "sheets": sheets, "columns": cols, "multi": n_tables > 1}


# =================================================================== schema helpers
def S(max_len=TEXT_MAX):
    return {"type": "string"} if max_len is None else {"type": "string", "maxLength": max_len}


N = {"type": "number"}
I = {"type": "integer"}
B = {"type": "boolean"}


def E(*vals):
    return {"enum": list(vals)}


def A(item):
    return {"type": "array", "items": item}


def O(props, required=()):
    """A closed object. Properties are written in this order (required ones first) by llama.cpp and Anthropic."""
    return {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}


def any_of(*schemas):
    return {"anyOf": list(schemas)}


COLOR = S(40)
COLOR_MAP = {"type": "object", "additionalProperties": COLOR}           # {"R3": "red"}
NUM_OR_TEXT = any_of(N, S(40))                  # axis limits on dates are text
BINS = any_of(I, A(N), O({"width": N, "min": N, "max": N, "edges": A(N), "closed": E("left", "right")}))
ASKS = A(O({"ask": S(), "how": E(*HOWS)}, required=("ask", "how")))
TITLE = any_of(S(), O({"text": S(), "size": N, "color": COLOR}))
OUTPUT_OBJ = O({"format": any_of(E(*FORMATS), A(E(*FORMATS))), "name": S(80)})
OUTPUT = any_of(E(*FORMATS), OUTPUT_OBJ)          # charts; plotkit (curves) needs the object
READ = O({"header_row": I, "data_start_row": I, "sep": S(10), "decimal": E(".", ","), "encoding": S(20)})
LEGEND_CHART = any_of(E(*LEGEND), B, O({"where": E(*LEGEND), "show": B, "size": N, "title": S()}))
LEGEND_CURVE = any_of(E(*LEGEND), B, O({"where": E(*LEGEND), "show": B, "size": N}))


def _files(info):
    f = E(*info["files"])
    return any_of(f, A(f))


def _sheets(info):
    s = E(*(info["sheets"] + ["all"]))
    return any_of(s, I, A(any_of(E(*info["sheets"]), I)))


def _col(info, free):
    return S(120) if free else E(*info["columns"])


def _hatch(props, hatch):
    if hatch == "code":
        props["code"] = S(CODE_MAX)
    elif hatch == "echarts":
        props["echarts"] = {"type": "object"}          # checked by plotkit_echarts.validate_patch


def _place_asks(props, required, asks):
    """asks "last" (as the prompt examples write it): optional, after everything else.
    asks "first": required, so the grammar makes the model list the asks right after file/chart (a small plan)."""
    if asks == "first":
        props = {k: props[k] for k in list(props)[:2]} | {"asks": ASKS} | {k: v for k, v in list(props.items())[2:]}
        return props, list(required) + ["asks"]
    props["asks"] = ASKS
    return props, list(required)


# =================================================================== charts (chartkit)
def chart_schema(info, hatch=None, asks="last", derived=False):
    """derived=True: the spec starts with data_code, which may add columns, so column names are free text."""
    col = _col(info, derived)
    ycol = any_of(col, E("count"), A(col))
    axis = {"label": S(), "min": NUM_OR_TEXT, "max": NUM_OR_TEXT, "step": N, "log": B, "flip": B, "rotate": N,
            "format": S(40), "agg": E(*AGGS), "period": E(*PERIODS), "order": A(any_of(S(80), N)), "bins": BINS,
            "label_size": N, "tick_size": N, "date_format": S(40)}
    x = any_of(col, O({"col": col, **axis}))
    y = any_of(col, E("count"), A(any_of(col, O({"col": col, "label": S()}, required=("col",)))),
               O({"col": ycol, **axis}))
    # data_code comes right after chart in both branches, so the grammar can keep both open until a column is named
    props = {"file": _files(info), "chart": E(*KINDS), "data_code": S(CODE_MAX), "sheets": _sheets(info), "read": READ}
    props |= {
        "x": x, "y": y,
        "by": any_of(col, O({"col": col, "order": A(any_of(S(80), N)), "colors": any_of(A(COLOR), COLOR_MAP)})),
        "z": any_of(col, E("count"), O({"col": any_of(col, E("count")), **axis})),
        "filter": any_of(S(200), A(S(200))),
        "stack": B, "sort": any_of(E("desc", "asc", "x"), A(any_of(S(80), N))), "top": I,
        "smooth": any_of(I, O({"window": I, "raw": B})),
        "values": any_of(B, S(40)),
        "colors": any_of(E("mono"), A(COLOR), COLOR_MAP),
        "highlight": any_of(S(80), N, A(any_of(S(80), N))),
        "ref": A(O({"x": NUM_OR_TEXT, "y": NUM_OR_TEXT, "text": S(), "color": COLOR, "linestyle": E(*LINESTYLES)})),
        "trend": any_of(B, O({"label": B})),
        "corr": any_of(E("all"), A(col)),
        "bins": BINS, "density": B, "error": E("std", "sem", "minmax"), "percent": B,
        "orient": E("h", "v"), "cmap": S(30), "point_size": N, "alpha": N,
        "title": TITLE, "legend": LEGEND_CHART, "size": A(N), "dpi": I, "font": S(60), "font_size": N,
        "text_color": COLOR, "grid": B, "output": OUTPUT}
    _hatch(props, hatch)
    props, req = _place_asks(props, ("file", "chart") + (("data_code",) if derived else ()), asks)
    return O(props, required=req)


# =================================================================== curves (plotkit)
def curve_schema(info, hatch=None, asks="last"):
    col = _col(info, False)
    axis = {"col": col, "label": S(), "min": N, "max": N, "step": N, "log": B, "label_size": N, "label_color": COLOR,
            "tick_size": N, "tick_color": COLOR, "minor": B, "invert": B}
    yaxis = {**axis, "color": COLOR, "width": N, "linestyle": E(*LINESTYLES), "style": E("line", "scatter", "line+marker"),
             "flip": E("none", "flip", "peaks_up", "peaks_down"), "legend": S(), "show": B}
    annot = O({"type": E(*sorted(pk.ANNOT_TYPES)), "on": E("y1", "y2"), "x": N, "y": N, "method": E("nearest", "interp"),
               "text": S(), "color": COLOR, "size": N, "count": I, "kind": E("max", "min"), "x_min": N, "x_max": N,
               "min_rel": N, "where": E(*CORNERS), "marker": any_of(B, S(20)), "linestyle": E(*LINESTYLES), "alpha": N})
    props = {"file": _files(info), "sheets": _sheets(info), "preset": E("tga", "none"), "read": READ,
             "data_code": S(CODE_MAX),
             "x": any_of(col, O(axis)), "y1": any_of(col, O(yaxis)), "y2": any_of(E(False), col, O(yaxis)),
             "annotate": {"type": "object", "additionalProperties": any_of(B, annot)},
             "title": TITLE, "legend": LEGEND_CURVE, "text_color": COLOR, "tick_direction": E("in", "out", "inout"),
             "grid": B, "size": A(N), "dpi": I, "font": S(60), "font_size": N, "combine": B,
             "colors": any_of(E("mono"), A(COLOR)), "names": A(S()), "offset": N, "panels": E("split"),
             "output": OUTPUT_OBJ}
    _hatch(props, hatch)
    props, req = _place_asks(props, ("file",), asks)
    return O(props, required=req)


# =================================================================== the flat profile
CHART_COLS = ("x.col", "y.col", "by.col", "z.col", "corr")
CURVE_COLS = ("x.col", "y1.col", "y2.col")
_CHART_AXIS = ("label", "min", "max", "step", "log", "flip", "rotate", "format", "agg", "period", "order", "bins",
               "bins.width", "bins.min", "bins.max", "bins.edges", "label_size", "tick_size", "date_format")
_CURVE_AXIS = ("label", "min", "max", "step", "log", "label_size", "label_color", "tick_size", "tick_color", "minor",
               "invert")
_CURVE_Y = _CURVE_AXIS + ("color", "width", "linestyle", "style", "flip", "legend", "show")
_COMMON = ("read.header_row", "read.data_start_row", "read.sep", "read.decimal", "read.encoding", "data_code",
           "title.text", "title.size", "title.color", "legend.where", "legend.show", "legend.size", "size", "dpi",
           "font", "font_size", "text_color", "grid", "output.format", "output.name", "colors")
CHART_KEYS = (_COMMON + tuple(f"{a}.{k}" for a in ("x", "y") for k in _CHART_AXIS)
              + tuple(f"z.{k}" for k in _CHART_AXIS)
              + ("by.order", "filter", "stack", "sort", "top", "smooth", "smooth.window",
                 "smooth.raw", "values", "highlight", "trend", "trend.label", "bins", "bins.width", "bins.min",
                 "bins.max", "bins.edges", "density", "error", "percent", "orient", "cmap", "point_size", "alpha",
                 "legend.title"))
CURVE_KEYS = (_COMMON + tuple(f"x.{k}" for k in _CURVE_AXIS) + tuple(f"{a}.{k}" for a in ("y1", "y2") for k in _CURVE_Y)
              + ("preset", "tick_direction", "combine", "names", "offset", "panels"))
ANNOT_FIELDS = ("show", "type", "on", "x", "y", "method", "text", "color", "size", "count", "kind", "x_min", "x_max",
                "min_rel", "where", "marker", "linestyle", "alpha")
SCALAR = {"string": {"type": "string"}, "number": N, "boolean": B}
FLAT_VALUE = any_of(SCALAR["string"], N, B, A(any_of(SCALAR["string"], N)))


def _uniq(seq):
    return list(dict.fromkeys(seq))


def flat_schema(info, kinds=("curve", "chart"), hatch=None, asks="last"):
    """Closed objects only, no string lengths, 0 optional parameters, 6 anyOf (Anthropic structured outputs)."""
    cols = _uniq((CHART_COLS if "chart" in kinds else ()) + (CURVE_COLS if "curve" in kinds else ()))
    keys = _uniq((CHART_KEYS if "chart" in kinds else ()) + (CURVE_KEYS if "curve" in kinds else ())
                 + ((hatch,) if hatch else ()))
    shapes = [O({"key": E(*cols), "column": E(*(info["columns"] + ["count", "all"]))}, required=("key", "column")),
              O({"key": E(*keys), "value": FLAT_VALUE}, required=("key", "value")),
              O({"sheet": any_of(E(*(info["sheets"] + ["all"])), I)}, required=("sheet",))]
    if "chart" in kinds:
        shapes.insert(1, O({"key": E(*cols), "new_column": {"type": "string"}}, required=("key", "new_column")))
        shapes.append(O({"color_of": {"type": "string"}, "color": {"type": "string"}}, required=("color_of", "color")))
        shapes.append(O({"series": {"type": "string"}, "name": {"type": "string"}}, required=("series", "name")))
        shapes.append(O({"ref_axis": E("x", "y"), "at": any_of(N, SCALAR["string"]), "text": {"type": "string"}},
                        required=("ref_axis", "at", "text")))
    if "curve" in kinds:
        shapes.append(O({"annotate": {"type": "string"}, "field": E(*ANNOT_FIELDS),
                         "value": any_of(N, SCALAR["string"], B)}, required=("annotate", "field", "value")))
    chart = E(*([*KINDS] if "chart" in kinds else []) + (["curve"] if "curve" in kinds else []))
    asks_s = A(O({"ask": {"type": "string"}, "how": E(*HOWS)}, required=("ask", "how")))
    props = {"file": any_of(E(*info["files"]), A(E(*info["files"]))), "chart": chart}
    props |= {"asks": asks_s, "settings": A(any_of(*shapes))} if asks == "first" else \
             {"settings": A(any_of(*shapes)), "asks": asks_s}
    return O(props, required=list(props))


def _set(d, path, value, repeat_ok):
    parts = path.split(".")
    for i, p in enumerate(parts[:-1]):
        cur = d.get(p)
        if cur is True or cur is None:
            d[p] = {}
        elif not isinstance(cur, dict):
            if p == "smooth" and isinstance(cur, (int, float)):
                d[p] = {"window": cur}
            elif p == "bins" and isinstance(cur, (int, float)):
                d[p] = {}
            else:
                raise ValueError(f'settings: "{".".join(parts[:i + 1])}" is a value, so "{path}" cannot be set')
        d = d[p]
    last = parts[-1]
    if last in d and repeat_ok:
        d[last] = (d[last] if isinstance(d[last], list) else [d[last]]) + (value if isinstance(value, list) else [value])
    elif last in d and isinstance(d[last], dict) and not isinstance(value, dict):
        raise ValueError(f'settings: "{path}" is set twice')
    else:
        d[last] = value


def flat_to_spec(flat):
    """The model's flat reply -> a plotkit / chartkit spec. Raises ValueError (sent back to the model) on conflicts."""
    if not isinstance(flat, dict) or "settings" not in flat:
        raise ValueError('the reply needs "file", "chart", "settings" and "asks"')
    spec = {"file": flat.get("file")}
    if flat.get("chart") not in (None, "curve"):
        spec["chart"] = flat["chart"]
    sheets, refs, annot, cmap, names = [], [], {}, {}, {}
    for s in flat.get("settings") or []:
        if not isinstance(s, dict):
            raise ValueError(f"settings: {s!r} is not an object")
        if "series" in s:
            names[s["series"]] = s["name"]
        elif "color_of" in s:
            cmap[s["color_of"]] = s["color"]
        elif "sheet" in s:
            sheets.append(s["sheet"])
        elif "ref_axis" in s:
            r = {s["ref_axis"]: s["at"]}
            if s.get("text"):
                r["text"] = s["text"]
            refs.append(r)
        elif "annotate" in s:
            a = annot.setdefault(s["annotate"], {})
            if s["field"] == "show":
                annot[s["annotate"]] = s["value"] if s["value"] is False or not a else a
            elif isinstance(a, dict):
                a[s["field"]] = s["value"]
        else:
            key = s.get("key")
            val = s["column"] if "column" in s else s["new_column"] if "new_column" in s else s.get("value")
            if key == "echarts" and isinstance(val, str):
                try:
                    val = json.loads(val)
                except json.JSONDecodeError as e:
                    raise ValueError(f'settings: "echarts" is not a JSON object ({e})') from None
            _set(spec, key, val, repeat_ok=key in ("y.col", "corr", "filter", "x.order", "y.order", "by.order"))
    if sheets:
        spec["sheets"] = sheets[0] if len(sheets) == 1 else sheets
    if refs:
        spec["ref"] = refs
    if cmap:
        if spec.get("colors") not in (None, {}) and not isinstance(spec.get("colors"), dict):
            raise ValueError('settings: "colors" is set both as a list and per category')
        spec["colors"] = {**(spec.get("colors") or {}), **cmap}
    if annot:
        spec["annotate"] = {k: (True if v == {} else v) for k, v in annot.items()}
    for k in ("x", "y", "y1", "y2", "by", "z"):         # {"col": "B"} alone -> "B", as the prompt writes it
        v = spec.get(k)
        if isinstance(v, dict) and list(v) == ["col"]:
            spec[k] = v["col"]
    if spec.get("y") == "count" or (isinstance(spec.get("y"), dict) and spec["y"].get("col") == "count"):
        spec["y"] = "count" if spec.get("y") == "count" else {**spec["y"], "col": "count"}
    if isinstance(spec.get("y2"), dict) and spec["y2"].get("show") is False and len(spec["y2"]) == 1:
        spec["y2"] = False
    if names:                                        # legend names of the y columns
        y = spec.get("y")
        ycols = y if isinstance(y, list) else [y.get("col")] if isinstance(y, dict) else [y]
        if isinstance(y, dict) and isinstance(y.get("col"), list):
            ycols = y["col"]
        spec["y"] = [{"col": c, "label": names[c]} if c in names else c for c in ycols]
    for k, short in (("title", "text"), ("legend", "where")):
        if isinstance(spec.get(k), dict) and list(spec[k]) == [short]:
            spec[k] = spec[k][short]
    if isinstance(spec.get("corr"), list) and spec["corr"] == ["all"]:
        spec["corr"] = "all"
    if isinstance(spec.get("colors"), list) and spec["colors"] == ["mono"]:
        spec["colors"] = "mono"
    if flat.get("asks"):
        spec["asks"] = flat["asks"]
    return spec


def spec_to_flat(spec, columns=None):
    """The inverse (for tests and examples): a spec -> the flat reply. Shorthands become dotted paths.
    columns: the enum columns; any other column name is written as a new_column (made by data_code)."""
    out = {"file": spec.get("file"), "chart": spec.get("chart", "curve"), "settings": [], "asks": spec.get("asks", [])}
    st = out["settings"]
    cols = set(CHART_COLS if "chart" in spec else CURVE_COLS)

    def put(path, v):
        if path in cols or path.endswith(".col"):
            for c in (v if isinstance(v, list) else [v]):
                if isinstance(c, dict):                # {"col", "label"} items of a y list
                    if c.get("label"):
                        st.append({"series": c.get("col"), "name": c["label"]})
                    c = c.get("col")
                new = columns is not None and c not in columns and c not in ("count", "all")
                st.append({"key": path, ("new_column" if new else "column"): c})
        else:
            st.append({"key": path, "value": json.dumps(v, ensure_ascii=False) if path == "echarts" else v})

    def walk(prefix, v):
        if isinstance(v, dict) and prefix not in ("echarts",):
            for k, vv in v.items():
                walk(f"{prefix}.{k}", vv)
        else:
            put(prefix, v)

    for k, v in spec.items():
        if k in ("file", "chart", "asks"):
            continue
        if k == "sheets":
            for s in (v if isinstance(v, list) else [v]):
                st.append({"sheet": s})
        elif k == "ref":
            for r in v:
                ax = "x" if "x" in r else "y"
                st.append({"ref_axis": ax, "at": r[ax], "text": r.get("text", "")})
        elif k == "annotate":
            for name, a in v.items():
                if a is False or a is True:
                    st.append({"annotate": name, "field": "show", "value": a})
                else:
                    for f, fv in a.items():
                        st.append({"annotate": name, "field": f, "value": fv})
        elif k in ("x", "y", "y1", "y2", "by", "z") and not isinstance(v, dict):
            if v is False:
                put(f"{k}.show", False)
            elif v == "count" and k in ("y", "z"):
                put(f"{k}.col", "count")
            else:
                put(f"{k}.col", v)
        elif k == "title" and isinstance(v, str):
            put("title.text", v)
        elif k == "legend" and not isinstance(v, dict):
            put("legend.show" if isinstance(v, bool) else "legend.where", v)
        elif k == "output" and isinstance(v, str):
            put("output.format", v)
        elif k == "colors" and isinstance(v, dict):
            for cat, c in v.items():
                st.append({"color_of": str(cat), "color": c})
        elif k in ("smooth", "trend", "bins", "colors") or not isinstance(v, dict):
            walk(k, v) if isinstance(v, dict) and k != "colors" else put(k, v)
        else:
            walk(k, v)
    return out


# =================================================================== building, checking, limits
def build(info, kinds=("curve", "chart"), hatch=None, profile="full", asks="last"):
    """The schema for one request. kinds: what the prompt allows ("curve" for AGENT.md, both for prompts/v2).
    hatch: "code" (matplotlib prompt), "echarts" (ECharts prompt) or None."""
    if profile == "flat":
        return flat_schema(info, kinds, hatch, asks)
    if profile not in ("full", "full2"):
        raise ValueError(f"unknown schema profile {profile!r}")
    alts = []
    if "curve" in kinds:
        alts.append(curve_schema(info, hatch, asks))
    if "chart" in kinds:
        charts = [chart_schema(info, hatch, asks), chart_schema(info, hatch, asks, derived=True)]
        alts += charts
        if profile == "full2":
            alts += [_sheets_first(c) for c in charts]
    return alts[0] if len(alts) == 1 else any_of(*alts)


def _sheets_first(chart):
    """The same chart branch, but written file, sheets, chart, ... . Grammars write required properties first and in
    order, so the plain branch (required file, chart) cannot take a reply that names the sheet before the chart kind:
    such a reply gets pushed into the curve branch. Adding this order keeps the accepted specs the same (profile
    "full2"; JSON Schema validation ignores key order)."""
    props = chart["properties"]
    head = {"file": props["file"], "sheets": props["sheets"], "chart": props["chart"]}
    rest = {k: v for k, v in props.items() if k not in head}
    req = ["file", "sheets", "chart"] + [r for r in chart["required"] if r not in ("file", "chart", "sheets")]
    return {**chart, "properties": head | rest, "required": req}


def validate(obj, schema, limit=3):
    """Short error messages ([] when obj fits). Needs the jsonschema package."""
    import jsonschema
    v = jsonschema.Draft202012Validator(schema)
    errs = sorted(v.iter_errors(obj), key=lambda e: len(list(e.absolute_path)))
    out = []
    for e in errs[:limit]:
        where = "/".join(str(p) for p in e.absolute_path) or "(top)"
        msg = e.message if len(e.message) < 160 else e.message[:157] + "..."
        out.append(f"{where}: {msg}")
    return out


def best_alternative_errors(obj, schema):
    """For a root anyOf, the errors of the alternative that comes closest (fewest errors)."""
    if "anyOf" not in schema:
        return validate(obj, schema)
    is_chart = isinstance(obj, dict) and "chart" in obj
    scored = [(len(errs), ("chart" in alt.get("properties", {})) != is_chart, i, errs)
              for i, alt in enumerate(schema["anyOf"]) for errs in [validate(obj, alt, limit=50)]]
    return min(scored)[3][:3]


def limits(schema):
    """Counts the Anthropic API limits apply to: optional properties and anyOf / type-array parameters."""
    st = {"optional": 0, "anyof": 0, "open_objects": 0, "string_limits": 0}

    def walk(s):
        if isinstance(s, dict):
            if s.get("type") == "object":
                props = s.get("properties") or {}
                st["optional"] += len([k for k in props if k not in (s.get("required") or [])])
                if s.get("additionalProperties") is not False:
                    st["open_objects"] += 1
            if "anyOf" in s or isinstance(s.get("type"), list):
                st["anyof"] += 1
            if "maxLength" in s or "minLength" in s:
                st["string_limits"] += 1
            for v in s.values():
                walk(v)
        elif isinstance(s, list):
            for v in s:
                walk(v)
    walk(schema)
    st["anthropic_ok"] = st["optional"] <= 24 and st["anyof"] <= 16 and not st["open_objects"] and not st["string_limits"]
    return st


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--root", default=".")
    ap.add_argument("--kinds", default="curve,chart")
    ap.add_argument("--hatch", choices=("code", "echarts"))
    ap.add_argument("--flat", action="store_true")
    ap.add_argument("--asks", choices=("last", "first"), default="last")
    ap.add_argument("--inspect", action="store_true", help="read files like plotkit inspect (TGA harness)")
    a = ap.parse_args()
    info = data_info(a.files, a.root, inspect=a.inspect)
    sch = build(info, tuple(a.kinds.split(",")), a.hatch, "flat" if a.flat else "full", a.asks)
    print(json.dumps(sch, ensure_ascii=False, indent=1))
    import sys
    print(json.dumps({"columns": len(info["columns"]), **limits(sch)}), file=sys.stderr)


if __name__ == "__main__":
    main()
