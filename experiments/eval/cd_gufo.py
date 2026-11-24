"""Make the constrained-decoding schemas acceptable to gufo (the Strix Halo server) without changing what they accept
much, and put their keys in the order the model writes them.

gufo's structured outputs (probed 2026-11-23, see EXPERIMENT_CD.md):
- `strict: true` needs every property required (OpenAI strict rules), so the kit's schemas go with `strict: false`;
- every enum/const needs an explicit `type` (a string, or a nullable type array);
- the root must be `type: object`: a root anyOf (curve | chart | chart with data_code) is refused;
- keys are generated in the schema's order; an optional key may be skipped but never written earlier, so a key the
  model writes "too late" is lost. The order therefore matters as much as the keys.

gufo(schema) = merge the root anyOf into one object (union of properties, intersection of required), add types,
then order every object's properties by the model's own writing order, measured on the free replies of the dev runs.

    python experiments/eval/cd_gufo.py      -> eval/results/key_order.json + offline check on the free dev specs
"""
import copy
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit/, tests/inputs, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
ORDER_FILE = HERE / "results" / "key_order.json"
FREE_RUNS = ("cnt_dev_a", "cnt_dev_b", "cnt_dev_c")


# =================================================================== the model's key order
def free_specs():
    csv.field_size_limit(10 ** 8)
    for name in FREE_RUNS:
        p = HERE / "results" / f"{name}.csv"
        if not p.exists():
            continue
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r["arm"] not in ("P-mpl", "P-ec") or r.get("ok_run") != "1":
                continue
            rec = HERE / r["run_dir"] / "record.json"
            if not rec.exists():
                continue
            for t in json.loads(rec.read_text(encoding="utf-8")).get("turns", []):
                sp = t.get("spec")
                if isinstance(sp, str):
                    try:
                        sp = json.loads(sp)
                    except json.JSONDecodeError:
                        continue
                if isinstance(sp, dict):
                    yield r["item"], r["arm"], sp


def _walk(obj, path, out):
    if isinstance(obj, dict):
        keys = list(obj)
        for i, k in enumerate(keys):
            out[path][k].append(i / max(1, len(keys) - 1))
            _walk(obj[k], f"{path}.{k}" if path else k, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, path + "[]", out)


def measure_order():
    """{path: {key: mean relative position (0 = first, 1 = last)}} over the free dev specs (aliases canonicalised)."""
    import cd
    pos = defaultdict(lambda: defaultdict(list))
    n = 0
    for _, _, sp in free_specs():
        _walk(canonical(sp, cd), "", pos)
        n += 1
    order = {p: {k: round(sum(v) / len(v), 4) for k, v in ks.items()} for p, ks in pos.items()}
    ORDER_FILE.parent.mkdir(parents=True, exist_ok=True)
    ORDER_FILE.write_text(json.dumps({"specs": n, "order": order}, ensure_ascii=False, indent=1), encoding="utf-8")
    return order


def canonical(sp, cd):
    """Top-level aliases the free replies use ("sheet") written as the canonical keys the schema has."""
    out = {}
    for k, v in sp.items():
        out["sheets" if k == "sheet" else k] = v
    return out


def load_order():
    return json.loads(ORDER_FILE.read_text(encoding="utf-8"))["order"] if ORDER_FILE.exists() else measure_order()


# =================================================================== schema transforms
def _type_of(v):
    return ("boolean" if isinstance(v, bool) else "integer" if isinstance(v, int) else "number"
            if isinstance(v, float) else "string" if isinstance(v, str) else "null" if v is None else None)


def add_types(node):
    if isinstance(node, list):
        return [add_types(x) for x in node]
    if not isinstance(node, dict):
        return node
    node = {k: add_types(v) for k, v in node.items()}
    vals = node.get("enum") if "enum" in node else ([node["const"]] if "const" in node else None)
    if vals is not None and "type" not in node:
        types = sorted({_type_of(v) for v in vals} - {None})
        if len(types) == 1:
            node["type"] = types[0]
        elif len(types) == 2 and "null" in types:
            node["type"] = [t for t in types if t != "null"] + ["null"]
        elif "enum" in node:                         # mixed values: one typed enum per type
            rest = {k: v for k, v in node.items() if k != "enum"}
            node = {**rest, "anyOf": [{"type": t, "enum": [v for v in vals if _type_of(v) == t]} for t in types]}
    return node


def _union(a, b):
    if a == b:
        return a
    alts = (a.get("anyOf") if isinstance(a, dict) and set(a) == {"anyOf"} else [a])
    for x in (b.get("anyOf") if isinstance(b, dict) and set(b) == {"anyOf"} else [b]):
        if x not in alts:
            alts = alts + [x]
    return {"anyOf": alts}


def merge_root(schema):
    """A root anyOf of objects -> one object: every key any branch allows, required = what every branch requires."""
    if "anyOf" not in schema:
        return schema
    props, req = {}, None
    for alt in schema["anyOf"]:
        for k, v in alt.get("properties", {}).items():
            props[k] = _union(props[k], v) if k in props else v
        r = set(alt.get("required", []))
        req = r if req is None else req & r
    return {"type": "object", "properties": props, "required": [k for k in props if k in (req or set())],
            "additionalProperties": False}


def reorder(node, order, path=""):
    """Order object properties by the model's writing order at that path; unseen keys keep their schema slot."""
    if isinstance(node, list):
        return [reorder(x, order, path) for x in node]
    if not isinstance(node, dict):
        return node
    node = dict(node)
    if "properties" in node:
        props = node["properties"]
        seen = order.get(path, {})
        n = max(1, len(props) - 1)
        rank = {k: (seen[k] if k in seen else i / n) for i, k in enumerate(props)}
        keys = sorted(props, key=lambda k: (rank[k], list(props).index(k)))
        node["properties"] = {k: reorder(props[k], order, f"{path}.{k}" if path else k) for k in keys}
        if "required" in node:          # gufo writes required keys in property order too; keep both lists aligned
            node["required"] = [k for k in keys if k in node["required"]]
    if "items" in node:
        node["items"] = reorder(node["items"], order, path + "[]")
    for k in ("anyOf", "oneOf", "allOf"):
        if k in node:
            node[k] = [reorder(x, order, path) for x in node[k]]
    return node


ANNOT_NAMES = ("residue", "peak", "peak2", "value", "value2", "vline1", "vline2", "vline3", "hline1", "hline2",
               "band1", "band2", "band3", "text1", "text2", "onset")


def _open(n):
    return isinstance(n, dict) and (n.get("type") == "object" or "additionalProperties" in n) and \
        ("properties" not in n or n.get("additionalProperties") is not False)


def close_open(node, order, path=""):
    """gufo needs every object closed with listed properties. annotate (a map of free names) gets the names seen in
    the free dev replies plus the usual ones; other open maps (colors by category, the free-form echarts patch) are
    dropped: an anyOf keeps its other alternatives (e.g. a colour list), a property with nothing left is removed."""
    if isinstance(node, list):
        return [close_open(x, order, path) for x in node]
    if not isinstance(node, dict):
        return node
    if _open(node):
        if path.endswith("annotate") and isinstance(node.get("additionalProperties"), dict):
            names = list(dict.fromkeys(list(order.get(path, {})) + list(ANNOT_NAMES)))
            val = close_open(node["additionalProperties"], order, path + ".*")
            return {"type": "object", "properties": {k: val for k in names}, "required": [], "additionalProperties": False}
        return None
    out = {}
    for k, v in node.items():
        if k == "properties":
            props = {}
            for pk, pv in v.items():
                c = close_open(pv, order, f"{path}.{pk}" if path else pk)
                if c is not None:
                    props[pk] = c
            out[k] = props
        elif k in ("anyOf", "oneOf"):
            alts = [a for a in (close_open(x, order, path) for x in v) if a is not None]
            if not alts:
                return None
            out[k] = alts
        elif k == "items":
            c = close_open(v, order, path + "[]")
            if c is None:
                return None
            out[k] = c
        else:
            out[k] = v
    if "required" in out and "properties" in out:
        out["required"] = [r for r in out["required"] if r in out["properties"]]
    if set(out) == {"anyOf"} and len(out["anyOf"]) == 1:
        return out["anyOf"][0]
    return out


def gufo(schema, order=None):
    order = load_order() if order is None else order
    return reorder(close_open(add_types(merge_root(copy.deepcopy(schema))), order), order)


# =================================================================== offline check
def in_order(obj, node, path=""):
    """Does a spec write its keys in the schema's order at every level (so an order-enforcing grammar keeps them)?"""
    if isinstance(obj, dict) and isinstance(node, dict):
        props = node.get("properties")
        if props is None:
            return all(in_order(obj, alt, path) for alt in node.get("anyOf", [])[:1]) if "anyOf" in node else True
        idx = [list(props).index(k) for k in obj if k in props]
        if idx != sorted(idx):
            return False
        return all(in_order(v, props[k]) for k, v in obj.items() if k in props)
    if isinstance(obj, list) and isinstance(node, dict) and "items" in node:
        return all(in_order(v, node["items"]) for v in obj)
    return True


def main():
    import cd
    import spec_schema as ss
    order = measure_order()
    items = json.loads((HERE / "cnt" / "dev" / "requests.json").read_text(encoding="utf-8"))
    items = {i["id"]: i for i in (items["items"] if isinstance(items, dict) else items)}
    n = acc_full = acc_g = ord_g = 0
    for item, arm, sp in free_specs():
        it = items.get(item)
        if not it:
            continue
        _, full = cd.schemas(it["files"], HERE / "cnt", ("curve", "chart"), cd.hatch_for(arm), "full")
        g = gufo(full, order)
        c = canonical(sp, cd)
        n += 1
        acc_full += not ss.validate(c, full)
        acc_g += not ss.validate(c, g)
        ord_g += in_order(c, g)
    print(f"free dev specs {n} (aliases canonical): accepted by full {acc_full}, by the gufo schema {acc_g}; "
          f"keys already in the gufo schema's order at every level: {ord_g} ({100 * ord_g / max(1, n):.0f}%)")
    print("top-level order:", sorted(order.get("", {}).items(), key=lambda kv: kv[1])[:14])


if __name__ == "__main__":
    main()
