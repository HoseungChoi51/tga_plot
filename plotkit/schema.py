"""The spec as a standalone JSON Schema (schema/plotkit.spec.schema.json) and a key reference (schema/SPEC.md).

Both are generated from the tables the normalizers use: the key names and defaults (plotkit.core.DEFAULTS,
plotkit.charts.TOP_KEYS / AXIS_KEYS), the aliases (core.TOP_ALIASES, AXIS_ALIASES, ANNOT_ALIASES,
charts.TOP_ALIASES, AXIS_EXTRA_ALIASES, KIND_ALIASES, AGG_ALIASES, PERIODS), the descriptions (core.SCHEMA_DOC,
charts.SCHEMA_DOC) and the ECharts patch allowlist (plotkit.echarts.ALLOWED). Only the JSON types are written here;
tests/test_schema.py checks that this file and the tables name the same keys.

The schema describes the canonical spec: the keys and values as plotkit names them. plotkit also accepts the
aliases, which the schema lists under "x-plotkit-aliases" (keys; a dotted target such as "output.format" is a key
inside an object) and "x-plotkit-value-aliases" (values); a model's reply is checked by plotkit.validate(), which
maps them and answers an error + hint. File, sheet and column names
are plain strings here (the per-request enums of the constrained-decoding study are in experiments/spec_schema.py).

    python -m plotkit schema --json > schema/plotkit.spec.schema.json
    python -m plotkit schema --md   > schema/SPEC.md
"""
import json
import re

from . import charts, core, echarts

# =================================================================== small builders
def S(desc=None, **kw):
    return _d({"type": "string", **kw}, desc)


def N(desc=None, **kw):
    return _d({"type": "number", **kw}, desc)


def I(desc=None, **kw):
    return _d({"type": "integer", **kw}, desc)


def B(desc=None):
    return _d({"type": "boolean"}, desc)


def E(vals, aliases=None, desc=None):
    out = {"enum": list(vals)}
    if aliases:
        out["x-plotkit-value-aliases"] = dict(sorted(aliases.items()))
    return _d(out, desc)


def A(item, desc=None, **kw):
    return _d({"type": "array", "items": item, **kw}, desc)


def ANY(*alts, desc=None):
    return _d({"anyOf": list(alts)}, desc)


def OBJ(props, aliases=None, desc=None, required=()):
    out = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        out["required"] = list(required)
    if aliases:
        out["x-plotkit-aliases"] = dict(sorted(aliases.items()))
    return _d(out, desc)


def REF(name):
    return {"$ref": f"#/$defs/{name}"}


def _d(s, desc):
    if desc:
        s["description"] = desc
    return s


# =================================================================== descriptions from SCHEMA_DOC
def doc_paths(table):
    """SCHEMA_DOC keys like "x|y1|y2.min / max" or "title / legend / size" -> {"x.min": text, ...}."""
    out = {}
    for key, text in table.items():
        parts = [p.strip() for p in key.split(" / ")]
        head = parts[0]
        if "." in head:
            prefix, first = head.rsplit(".", 1)
            leaves = [first] + parts[1:]
        else:
            prefix, leaves = "", parts
        for alt in prefix.split("|") if prefix else [""]:
            for leaf in leaves:
                path = f"{alt}.{leaf}" if alt else leaf
                out[path.replace("<name>", "*")] = text
    return out


CURVE_DOC = doc_paths(core.SCHEMA_DOC)
CHART_DOC = doc_paths(charts.SCHEMA_DOC)


def _doc(kind, path):
    table = CURVE_DOC if kind == "curve" else CHART_DOC
    return table.get(path)


# =================================================================== shared pieces
def _value_aliases(table, canonical):
    """{alias: canonical} from a table {spelling: canonical or code}."""
    return {k: v for k, v in table.items() if k not in canonical and v in canonical}


LINESTYLE_NAMES = ("solid", "dashed", "dotted", "dashdot")
LINESTYLE_ALIASES = {k: next(n for n in LINESTYLE_NAMES if core.LINESTYLES[n] == v)
                     for k, v in core.LINESTYLES.items() if k not in LINESTYLE_NAMES}
LEGEND_ALIASES = {k: v for k, v in core.KOREAN_PLACES.items()}
PERIOD_ALIASES = {k: next(n for n in charts.PERIOD_NAMES if charts.PERIODS[n] == v)
                  for k, v in charts.PERIODS.items() if k not in charts.PERIOD_NAMES}


def defs():
    color = S("a colour: a name (red, navy), a Korean name (빨강, 남색) or a hex code (#c0392b)",
              **{"x-plotkit-value-aliases": dict(sorted(core.KOREAN_COLORS.items()))})
    column = S("a column: its letter as in Excel (\"B\"; in text files A is the first field), its name, or part of its name",
               minLength=1)
    file = ANY(S(minLength=1), A(S(minLength=1), minItems=1),
               desc="data file path, or a list of paths (xlsx/xls/csv/txt/...); * and ? patterns are expanded")
    sheets = ANY(S(minLength=1), I(minimum=1), A(ANY(S(minLength=1), I(minimum=1)), minItems=1),
                 desc='"all", a sheet name, a 1-based sheet number, or a list of those')
    hows = ("key", "data_code", "code", "echarts", "unsupported")
    asks = A(OBJ({"ask": S("the user's ask, in their words"), "how": E(hows)}, required=("ask",)),
             desc=core.SCHEMA_DOC["asks"])
    read = OBJ(desc="how to read the files; normally automatic", props={"header_row": I(core.SCHEMA_DOC["read.header_row"], minimum=1),
                "data_start_row": I(core.SCHEMA_DOC["read.data_start_row"], minimum=1),
                "sep": S(core.SCHEMA_DOC["read.sep"]), "decimal": E((".", ","), desc=core.SCHEMA_DOC["read.decimal"]),
                "encoding": S(core.SCHEMA_DOC["read.encoding"])})
    fmt = E(core.FORMATS, aliases={"jpeg": "jpg", "tiff": "tif"})
    legend_where = E(core.LEGEND_PLACES, LEGEND_ALIASES, desc="where the legend goes")
    linestyle = E(LINESTYLE_NAMES, LINESTYLE_ALIASES, desc="line style")
    return {"legend_where": legend_where, "linestyle": linestyle, "color": color, "column": column, "file": file, "sheets": sheets, "asks": asks, "read": read,
            "format": fmt, "echarts": echarts_patch()}


# =================================================================== curves (plotkit.core)
def _curve_axis(ax):
    d = core.DEFAULTS[ax]
    p = {}
    for k in d:
        doc = _doc("curve", f"{ax}.{k}")
        t = {"col": REF("column"), "label": S(), "min": N(), "max": N(), "step": N(exclusiveMinimum=0), "log": B(),
             "label_size": N(), "label_color": REF("color"), "tick_size": N(), "tick_color": REF("color"),
             "minor": B(), "invert": B(), "color": REF("color"), "width": N(exclusiveMinimum=0),
             "linestyle": REF("linestyle"), "style": E(("line", "scatter", "line+marker")),
             "flip": E(("none", "flip", "peaks_up", "peaks_down")), "legend": S(), "show": B()}[k]
        p[k] = _with_default(_d(dict(t), doc) if "$ref" not in t else ({**t, "description": doc} if doc else t), d[k])
    aliases = {a: c for a, c in core.AXIS_ALIASES.items() if c in d and a != c}
    if ax == "x":
        aliases["flip"] = "invert"
    obj = OBJ(p, aliases, desc='also "range" / "lim" / "limits": [min, max] sets both')
    alts = [REF("column"), obj] + ([{"const": False, "description": "no second axis"}] if ax == "y2" else [])
    return ANY(*alts, desc=_doc("curve", ax) or f"the {ax} axis: a column, or an object")


def _with_default(s, default):
    if default not in (None, [], {}) and "default" not in s:
        s = {**s, "default": default}
    return s


def annotation():
    t = {"type": E(sorted(core.ANNOT_TYPES)), "on": E(("y1", "y2")), "x": N(), "y": N(),
         "method": E(("nearest", "interp")), "text": S(), "color": REF("color"), "size": N(), "count": I(minimum=1),
         "kind": E(("max", "min")), "x_min": N(), "x_max": N(), "min_rel": N(minimum=0),
         "where": E(("upper left", "upper right", "lower left", "lower right")),
         "marker": ANY(B(), S()), "linestyle": REF("linestyle"), "alpha": N(minimum=0, maximum=1)}
    props = {}
    for k in sorted(core.ANNOT_KEYS):
        doc = _doc("curve", f"annotate.*.{k}")
        s = t[k]
        props[k] = {**s, "description": doc} if doc and "$ref" in s else _d(dict(s), doc)
    obj = OBJ(props, {a: c for a, c in core.ANNOT_ALIASES.items() if c in core.ANNOT_KEYS and a != c})
    return {"type": "object", "additionalProperties": ANY(B(), obj), "description": core.SCHEMA_DOC["annotate.<name>"]}


def curve():
    d = core.DEFAULTS
    t = {
        "file": REF("file"), "sheets": REF("sheets"),
        "preset": E(("tga", "none")), "read": {**REF("read"), "description": "how to read the files; normally automatic"},
        "x": _curve_axis("x"), "y1": _curve_axis("y1"), "y2": _curve_axis("y2"),
        "annotate": annotation(),
        "title": ANY(S(), {"const": False}, OBJ({"text": S(), "size": N(), "color": REF("color")})),
        "legend": ANY(REF("legend_where"), B(),
                      OBJ({"where": REF("legend_where"), "show": B(), "size": N()})),
        "text_color": REF("color"), "tick_direction": E(("in", "out", "inout")),
        "code": ANY(S(), A(S())), "echarts": REF("echarts"), "grid": B(),
        "size": A(N(exclusiveMinimum=0), minItems=2, maxItems=2), "dpi": I(minimum=1), "font": S(),
        "font_size": N(exclusiveMinimum=0), "combine": B(),
        "colors": ANY({"const": "mono"}, A(REF("color"))), "names": A(S()), "offset": N(),
        "panels": E(("split",)), "data_code": ANY(S(), A(S())), "asks": REF("asks"),
        "output": OBJ({"dir": S(core.SCHEMA_DOC["output.dir"]),
                       "format": ANY(REF("format"), A(REF("format")), desc=core.SCHEMA_DOC["output.format"]),
                       "name": S(core.SCHEMA_DOC["output.name"])},
                      desc="the files to write; the host's folder and formats win (plotkit.render)"),
    }
    props = {}
    for k in d:
        s = dict(t[k])
        doc = _doc("curve", k)
        if doc and "description" not in s:
            s["description"] = doc
        props[k] = _with_default(s, d[k]) if not isinstance(d[k], dict) else s
    aliases = {a: c for a, c in core.TOP_ALIASES.items() if a != c}
    return OBJ(props, aliases, required=("file",),
               desc="An instrument curve (TGA and other x-y exports): x, a left axis y1 and a right axis y2.")


# =================================================================== charts (plotkit.charts)
def _chart_axis(role):
    t = {"col": ANY(REF("column"), A(REF("column"))), "label": S(), "min": ANY(N(), S()), "max": ANY(N(), S()),
         "step": N(exclusiveMinimum=0), "log": B(), "flip": B(), "rotate": N(), "format": S(),
         "agg": E(charts.AGGS, {a: c for a, c in charts.AGG_ALIASES.items() if c in charts.AGGS}),
         "period": E(charts.PERIOD_NAMES, PERIOD_ALIASES), "order": A(ANY(S(), N())),
         "bins": REF("bins"), "label_size": N(), "tick_size": N(), "date_format": S()}
    props = {k: t[k] for k in sorted(charts.AXIS_KEYS) if not k.startswith("_")}
    for k, s in props.items():
        doc = _doc("chart", f"{role}.{k}")
        if doc:
            props[k] = {**s, "description": doc}
    aliases = {}
    for a in {*core.AXIS_ALIASES, *charts.AXIS_EXTRA_ALIASES}:
        c = core.AXIS_ALIASES.get(a, a)
        c = charts.AXIS_EXTRA_ALIASES.get(c, c)
        if c in props and a != c:
            aliases[a] = c
    return OBJ(props, aliases, desc="a chart axis: x, y or z")


def chart():
    col = REF("column")
    t = {
        "file": REF("file"), "sheets": REF("sheets"), "read": REF("read"),
        "chart": E(charts.KINDS, {a: c for a, c in charts.KIND_ALIASES.items() if c in charts.KINDS}),
        "x": ANY(col, REF("chart_axis")),
        "y": ANY(col, {"const": "count"}, A(ANY(col, OBJ({"col": col, "label": S()}, required=("col",)))),
                 REF("chart_axis")),
        "by": ANY(col, OBJ({"col": col, "order": A(ANY(S(), N())), "colors": ANY(A(REF("color")), {
            "type": "object", "additionalProperties": REF("color")})})),
        "z": ANY(col, {"const": "count"}, REF("chart_axis")),
        "filter": ANY(S(), A(S())),
        "stack": B(), "sort": ANY(E(("desc", "asc", "x")), A(ANY(S(), N()))), "top": I(minimum=1),
        "smooth": ANY(I(minimum=1), OBJ({"window": I(minimum=1), "raw": B()})),
        "values": ANY(B(), S()),
        "colors": ANY({"const": "mono"}, A(REF("color")), {"type": "object", "additionalProperties": REF("color")}),
        "highlight": ANY(S(), N(), A(ANY(S(), N()))),
        "ref": A(OBJ({"x": ANY(N(), S()), "y": ANY(N(), S()), "text": S(), "color": REF("color"),
                      "linestyle": REF("linestyle")})),
        "trend": ANY(B(), OBJ({"label": B()})),
        "corr": ANY({"const": "all"}, A(col)),
        "bins": REF("bins"), "density": B(), "error": E(("std", "sem", "minmax")), "percent": B(),
        "orient": E(("h", "v")), "cmap": S(), "point_size": N(exclusiveMinimum=0), "alpha": N(minimum=0, maximum=1),
        "title": ANY(S(), OBJ({"text": S(), "size": N(), "color": REF("color")})),
        "legend": ANY(REF("legend_where"), B(),
                      OBJ({"where": REF("legend_where"), "show": B(), "size": N(), "title": S()})),
        "size": A(N(exclusiveMinimum=0), minItems=2, maxItems=2), "dpi": I(minimum=1), "font": S(),
        "font_size": N(exclusiveMinimum=0), "text_color": REF("color"), "grid": B(),
        "output": ANY(REF("format"), OBJ({"dir": S(), "format": ANY(REF("format"), A(REF("format"))), "name": S()})),
        "data_code": ANY(S(), A(S())), "code": ANY(S(), A(S())), "echarts": REF("echarts"), "asks": REF("asks"),
        "engine": E(core.ENGINES), "notes": S(),
    }
    props = {}
    for k in sorted(charts.TOP_KEYS, key=lambda k: (k not in ("file", "chart"), k)):
        s = dict(t[k])
        doc = _doc("chart", k)
        if doc and "description" not in s:
            s["description"] = doc
        props[k] = s
    aliases = {a: c for a, c in charts.TOP_ALIASES.items() if a != c}
    return OBJ(props, aliases, required=("file", "chart"),
               desc="A chart of table data (bar, hbar, line, scatter, histogram, heatmap, pie).")


# =================================================================== the ECharts patch
PATCH_PARTS = {"patch_style": "_STYLE", "patch_line": "_LINE", "patch_item": "_ITEM", "patch_label": "_LABEL",
               "patch_mark_item": "_MARK_ITEM", "patch_mark": "_MARK", "patch_axis": "_AXIS", "patch_series": "_SERIES",
               "patch_graphic": "_GRAPHIC"}


def _patch(node, top=False):
    """The allowlist as a schema; its shared parts (echarts._STYLE, _LINE, ...) become $defs/patch_*."""
    if not top and isinstance(node, dict):
        for name, attr in PATCH_PARTS.items():
            if node is getattr(echarts, attr):
                return REF(name)
    if node is None:
        return {"$ref": "#/$defs/patch_value"}
    if node == "MARKDATA":                       # markArea/markLine/markPoint data: items, or [start, end] pairs of items
        item = _patch(echarts._MARK_ITEM)
        return A(ANY(item, A(item, minItems=2, maxItems=2)))
    if isinstance(node, list):
        item = _patch(node[0])
        return ANY(item, A(item))
    return {"type": "object", "properties": {k: _patch(v) for k, v in node.items()}, "additionalProperties": False}


def patch_parts():
    return {name: _patch(getattr(echarts, attr), top=True) for name, attr in PATCH_PARTS.items()}


def echarts_patch():
    s = _patch(echarts.ALLOWED, top=True)
    s["description"] = core.SCHEMA_DOC["echarts"]
    return s


# =================================================================== the document
def schema():
    d = defs()
    d["patch_value"] = ANY({"type": ["string", "number", "boolean", "null"]},
                           A({"type": ["string", "number", "boolean", "null", "array", "object"]}),
                           desc="a plain value: text, a number, a colour, or a list of those; "
                                "no links, data URLs or functions")
    d["bins"] = ANY(I(minimum=1), A(N()), OBJ({"width": N(exclusiveMinimum=0), "min": N(), "max": N(),
                                                "edges": A(N()), "closed": E(("left", "right"))}),
                    desc=charts.SCHEMA_DOC["bins"])
    d["chart_axis"] = _chart_axis("x")
    d.update(patch_parts())
    d["curve"] = curve()
    d["chart"] = chart()
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "plotkit spec",
            "description": "What a model writes for plotkit: a curve (instrument export, x / y1 / y2) or a chart of "
                           "table data (a \"chart\" key). Generated by python -m plotkit schema --json; do not edit.",
            "x-plotkit-version": core.__version__,
            "oneOf": [REF("curve"), REF("chart")], "$defs": d}


def dumps():
    return json.dumps(schema(), ensure_ascii=False, indent=1) + "\n"


# =================================================================== SPEC.md
CHART_EXAMPLE = {"file": "run_log.xlsx", "sheets": "런로그", "chart": "bar", "x": "반응기",
                 "y": {"col": "CNT수율", "agg": "mean", "label": "평균 수율 (g/g-cat)"},
                 "filter": ["주차 >= 10"], "values": "{:.2f}",
                 "asks": [{"ask": "반응기별 평균 수율", "how": "key"}, {"ask": "10주차부터", "how": "key"}]}


def _type(s, d):
    """A short type name for the key reference."""
    if "$ref" in s:
        name = s["$ref"].split("/")[-1]
        return {"column": "column", "color": "colour", "file": "path or [paths]", "sheets": "sheet(s)",
                "asks": "[{ask, how}]", "read": "object", "format": "format", "echarts": "ECharts patch",
                "chart_axis": "axis object", "bins": "bins", "patch_value": "value",
                "legend_where": "legend place", "linestyle": "line style"}.get(name, name)
    if "anyOf" in s:
        return " | ".join(dict.fromkeys(_type(a, d) for a in s["anyOf"]))
    if "const" in s:
        return json.dumps(s["const"], ensure_ascii=False)
    if "enum" in s:
        return " | ".join(json.dumps(v, ensure_ascii=False) for v in s["enum"])
    t = s.get("type")
    if t == "array":
        return f"[{_type(s['items'], d)}]"
    if t == "object":
        return "object" if s.get("properties") else "{name: …}"
    return {"string": "text", "number": "number", "integer": "integer", "boolean": "true/false"}.get(t, str(t))


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _table(obj, d, prefix=""):
    aliases = {}
    for a, c in (obj.get("x-plotkit-aliases") or {}).items():
        aliases.setdefault(c, []).append(a)
    rows = ["| key | type | default | aliases | what it does |", "|---|---|---|---|---|"]
    for k, s in obj["properties"].items():
        default = "" if "default" not in s else f"`{json.dumps(s['default'], ensure_ascii=False)}`"
        va = s.get("x-plotkit-value-aliases")
        desc = s.get("description") or ""
        if va:
            desc += " Also accepted: " + ", ".join(f"{a} → {c}" for a, c in list(va.items())[:12]) + \
                    (" …" if len(va) > 12 else "") + "."
        al = ", ".join(f"`{a}`" for a in sorted(aliases.get(k, [])))
        rows.append(f"| `{prefix}{k}` | {_cell(_type(s, d))} | {_cell(default)} | {_cell(al)} | {_cell(desc)} |")
    return "\n".join(rows)


def markdown():
    s = schema()
    d = s["$defs"]
    curve, chart = d["curve"], d["chart"]
    out = ["# plotkit spec: key reference", "",
           "Generated by `python -m plotkit schema --md` from the same tables as `plotkit.spec.schema.json`; do not edit.",
           f"plotkit {core.__version__}.", "",
           "A spec is a JSON object the model writes. It is a **curve** (an instrument export: x, a left axis y1, a right "
           "axis y2; the TGA preset by default) or, with a `\"chart\"` key, a **chart** of table data. Every key is "
           "optional except `file` (and `chart` for charts); everything else has a default. plotkit also accepts the "
           "aliases listed and maps them; `plotkit.validate()` answers an unknown key or value with an error and a hint.",
           "", "Columns are given by letter (`\"B\"`, as in Excel; in text files A is the first field), by name, or by part "
           "of the name. Colours are names (`red`, `navy`), Korean names (`빨강`, `남색`) or hex codes.", "",
           "## Curves", "", curve["description"], "", "```json", json.dumps(core.EXAMPLE_SPEC, ensure_ascii=False, indent=1),
           "```", "", "### Top level", "", _table(curve, d)]
    for ax in ("x", "y1", "y2"):
        obj = next(a for a in curve["properties"][ax]["anyOf"] if a.get("type") == "object")
        out += ["", f"### `{ax}` (a column, or this object{', or false for none' if ax == 'y2' else ''})", "", _table(obj, d, f"{ax}.")]
    ann = curve["properties"]["annotate"]["additionalProperties"]["anyOf"][1]
    out += ["", "### `annotate.<name>`", "", curve["properties"]["annotate"]["description"], "", _table(ann, d, "annotate.<name>.")]
    out += ["", "### `read` (both kinds)", "", _table(d["read"], d, "read.")]
    out += ["", "### `output` (curves)", "", _table(curve["properties"]["output"], d, "output.")]
    out += ["", "## Charts", "", chart["description"], "", "```json", json.dumps(CHART_EXAMPLE, ensure_ascii=False, indent=1),
            "```", "", "### Top level", "", _table(chart, d),
            "", "### `x`, `y`, `z` (a column, or this object)", "", _table(d["chart_axis"], d, "x.")]
    out += ["", "## `asks`", "", d["asks"]["description"], "",
            "`how` is `key`, `data_code`, `code` (matplotlib only), `echarts` (ECharts only) or `unsupported`; "
            "plotkit returns the unsupported ones as `not_done`, for the app to tell the user.",
            "", "## The `echarts` patch", "", d["echarts"]["description"], "",
            "Allowed paths (anything else is refused with the allowed keys as the hint):", ""]
    for path in _patch_paths(echarts.ALLOWED):
        out.append(f"- `{path}`")
    return "\n".join(out) + "\n"


def _patch_paths(node, prefix=""):
    if isinstance(node, list):
        return _patch_paths(node[0], prefix + "[i]")
    if node is None:
        return [prefix]
    if node == "MARKDATA":
        return _patch_paths(echarts._MARK_ITEM, prefix + "[i]")
    out = []
    groups = {}
    for k, v in node.items():
        if v is None:
            groups.setdefault(prefix, []).append(k)
        else:
            out += _patch_paths(v, f"{prefix}.{k}" if prefix else k)
    leaf = [f"{p}.{{{', '.join(ks)}}}" if p else ", ".join(ks) for p, ks in groups.items()]
    return leaf + out
