"""The standalone schema (schema/): up to date, in step with the normalizers, and true to the reference specs."""
import json
import sys
from pathlib import Path

import pytest

import plotkit
from plotkit import charts, core, schema

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = schema.schema()
DEFS = SCHEMA["$defs"]
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


def props(name):
    return DEFS[name]["properties"]


def curve_axis(ax):
    return next(a for a in DEFS["curve"]["properties"][ax]["anyOf"] if a.get("type") == "object")


# =================================================================== the files in schema/
def test_schema_is_a_valid_json_schema():
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


def test_committed_files_are_up_to_date():
    assert (ROOT / "schema" / "plotkit.spec.schema.json").read_text(encoding="utf-8") == schema.dumps(), \
        "run: python -m plotkit schema --json > schema/plotkit.spec.schema.json"
    assert (ROOT / "schema" / "SPEC.md").read_text(encoding="utf-8") == schema.markdown(), \
        "run: python -m plotkit schema --md > schema/SPEC.md"


# =================================================================== drift: the schema names the keys the normalizers take
def test_curve_keys_match_the_defaults():
    assert set(props("curve")) == set(core.DEFAULTS)
    for ax in ("x", "y1", "y2"):
        assert set(curve_axis(ax)["properties"]) == set(core.DEFAULTS[ax])
    for k in ("read", "output"):
        p = DEFS["read"]["properties"] if k == "read" else props("curve")["output"]["properties"]
        assert set(p) == set(core.DEFAULTS[k])
    ann = props("curve")["annotate"]["additionalProperties"]["anyOf"][1]["properties"]
    assert set(ann) == core.ANNOT_KEYS


def test_chart_keys_match_the_tables():
    assert set(props("chart")) == charts.TOP_KEYS
    assert set(props("chart_axis")) == {k for k in charts.AXIS_KEYS if not k.startswith("_")}


def test_every_alias_names_a_schema_key():
    for name, table, allowed in (("curve", core.TOP_ALIASES, set(core.DEFAULTS)),
                                 ("chart", charts.TOP_ALIASES, set(charts.TOP_KEYS))):
        listed = DEFS[name]["x-plotkit-aliases"]
        for alias, target in table.items():
            if alias == target:
                continue
            assert listed.get(alias) == target, (name, alias)
            assert target.split(".")[0] in allowed, (name, alias, target)


def _sample(s):
    """A value that fits schema s (the simplest one)."""
    if "$ref" in s:
        name = s["$ref"].split("/")[-1]
        return "black" if name == "color" else _sample(DEFS[name])
    if "anyOf" in s:
        return _sample(s["anyOf"][0])
    if "const" in s:
        return s["const"]
    if "enum" in s:
        return s["enum"][0]
    t = s.get("type")
    if t == "array":
        return [_sample(s["items"])] * (s.get("minItems") or 1)
    return {"string": "B", "number": 1, "integer": 1, "boolean": True, "object": {}}[t]


TGA = str(ROOT / "tests" / "inputs" / "TGA.xlsx")
LOG = str(ROOT / "tests" / "inputs" / "run_log.csv")


@pytest.mark.parametrize("key", sorted(core.DEFAULTS))
def test_every_curve_key_is_accepted(key):
    if key in ("file", "code", "echarts", "data_code"):
        pytest.skip("drawn, not just checked")
    value = {"sheets": 1, "preset": "tga", "panels": "split"}.get(key, _sample(props("curve")[key]))
    core.normalize_spec({"file": TGA, key: value})


@pytest.mark.parametrize("key", sorted(charts.TOP_KEYS))
def test_every_chart_key_is_accepted(key):
    if key in ("file", "chart", "code", "echarts", "data_code"):
        pytest.skip("drawn, not just checked")
    base = {"file": LOG, "chart": "bar", "x": "반응기", "y": "수율"}
    value = {"x": "반응기", "y": "수율", "by": "등급", "z": "수율", "sort": "desc"}.get(key, _sample(props("chart")[key]))
    charts.normalize({**base, key: value})


def test_an_unknown_key_is_refused_by_both():
    with pytest.raises(plotkit.PlotkitError):
        core.normalize_spec({"file": TGA, "not_a_key": 1})
    with pytest.raises(plotkit.PlotkitError):
        charts.normalize({"file": LOG, "chart": "bar", "not_a_key": 1})
    assert not VALIDATOR.is_valid({"file": "a.xlsx", "not_a_key": 1})


def test_every_key_has_a_description():
    missing = [f"curve.{k}" for k, v in props("curve").items() if "description" not in v] + \
              [f"chart.{k}" for k, v in props("chart").items() if "description" not in v]
    assert not missing, missing


# =================================================================== the reference specs validate
def reference_specs():
    out = {}
    for rid, s in json.loads((ROOT / "tests" / "reference_specs.json").read_text(encoding="utf-8")).items():
        if not rid.startswith("_") and isinstance(s, dict):
            out[f"A {rid}"] = s
    refb = ROOT / "experiments" / "eval" / "reference_b.json"
    if refb.exists():
        for rid, s in json.loads(refb.read_text(encoding="utf-8")).items():
            if not rid.startswith("_") and isinstance(s, dict):
                out[f"B {rid}"] = s
    dev = ROOT / "experiments" / "eval"
    if (dev / "cnt_dev_refs.py").exists():
        sys.path.insert(0, str(dev))
        try:
            from cnt_dev_refs import REFS
        finally:
            sys.path.remove(str(dev))
        out.update({f"CNT {k}": v for k, v in REFS.items()})
    return out


REFS = reference_specs()


@pytest.mark.parametrize("rid", sorted(REFS))
def test_reference_spec_validates(rid):
    errors = sorted(VALIDATOR.iter_errors(REFS[rid]), key=lambda e: e.path)
    assert not errors, [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors[:3]]


def test_kinds_aggs_periods_are_shared():
    sys.path.insert(0, str(ROOT / "experiments"))
    try:
        import spec_schema
    finally:
        sys.path.remove(str(ROOT / "experiments"))
    assert spec_schema.KINDS == charts.KINDS and spec_schema.AGGS == charts.AGGS
    assert spec_schema.PERIODS == charts.PERIOD_NAMES


def test_the_examples_in_spec_md_validate():
    assert VALIDATOR.is_valid(core.EXAMPLE_SPEC)
    assert VALIDATOR.is_valid(schema.CHART_EXAMPLE)
