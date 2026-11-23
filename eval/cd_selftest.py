"""Offline checks of the constrained-decoding schemas (no model needed).

    python eval/cd_selftest.py                 # all checks; writes eval/results/cd_selftest.json

1. columns   every enum column name / letter resolves to exactly one column with chartkit / plotkit
2. replay    every spec that PASSED in the dev runs (eval/results/runs/cnt_dev_*), the TGA reference specs and the
             Set B reference answers: (a) does the spec the model wrote fit the schema as written ("raw"), and
             (b) after rewriting aliases to canonical keys ("canonical")? (b) must be ~100%: a correct spec the grammar
             cannot express is a protocol regression. (a) is what the grammar changes for the free model.
3. flat      spec -> flat -> spec round trip for the same specs, checked with chartkit.normalize /
             plotkit.normalize_spec, and every flat form validated against the flat schema
4. limits    Anthropic limits of every flat schema (optional parameters, anyOf, closed objects)
Whether a real server compiles and enforces the schemas is checked by eval/cd_preflight.py (needs the server).
"""
import argparse
import collections
import copy
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import chartkit  # noqa: E402
import plotkit as pk  # noqa: E402
import spec_schema as ss  # noqa: E402

CNT = HERE / "cnt"


def canonical(spec):
    """Aliases -> canonical keys, the way chartkit / plotkit read them (what the grammar would have forced)."""
    s = copy.deepcopy(spec)
    is_chart = any(k in s for k in ("chart", "kind", "chart_type", "type", "plot"))
    al = chartkit.TOP_ALIASES if is_chart else pk.TOP_ALIASES
    out = {}
    for k, v in s.items():
        kk = al.get(k, al.get(str(k).lower(), k))
        if kk == "output.format":
            out.setdefault("output", {})["format"] = v
            continue
        if "." in kk:
            a, b = kk.split(".", 1)
            out.setdefault(a, {})[b] = v
            continue
        out[kk] = v
    axes = ("x", "y", "z") if is_chart else ("x", "y1", "y2")
    for ax in axes:
        if isinstance(out.get(ax), dict):
            out[ax] = {pk.AXIS_ALIASES.get(k, k): v for k, v in out[ax].items()}
    if is_chart and isinstance(out.get("chart"), str):
        out["chart"] = chartkit.KIND_ALIASES.get(out["chart"].lower(), out["chart"].lower())
    if not is_chart and isinstance(out.get("annotate"), dict):
        out["annotate"] = {n: ({pk.ANNOT_ALIASES.get(k, k): v for k, v in a.items()} if isinstance(a, dict) else a)
                           for n, a in out["annotate"].items()}
    if isinstance(out.get("y"), dict) and isinstance(out["y"].get("agg"), str):
        out["y"]["agg"] = chartkit.AGG_ALIASES.get(out["y"]["agg"].lower(), out["y"]["agg"].lower())
    out.pop("engine", None)
    out.pop("notes", None)
    if isinstance(out.get("output"), dict):
        out["output"].pop("dir", None)
        if not out["output"]:
            out.pop("output")
    return out


def hatch_of(arm):
    return "echarts" if arm.startswith("P-ec") else "code"


# =================================================================== the specs to replay
def dev_specs():
    """(label, files, root, kinds, hatch, spec) for every passing turn of the dev runs, deduplicated."""
    reqs = {i["id"]: i for i in json.loads((CNT / "dev" / "requests.json").read_text(encoding="utf-8"))["items"]}
    seen, out = set(), []
    for p in sorted(glob.glob(str(HERE / "results" / "runs" / "cnt_dev_*" / "P-*" / "*" / "record.json"))):
        rec = json.loads(Path(p).read_text(encoding="utf-8"))
        item = reqs.get(rec["item"])
        if not item:
            continue
        for t in rec["turns"]:
            if not (t.get("check") or {}).get("pass") or not isinstance(t.get("spec"), dict):
                continue
            spec = {k: v for k, v in t["spec"].items() if not (k == "output" and isinstance(v, dict) and set(v) <= {"dir"})}
            key = (rec["arm"], json.dumps(spec, sort_keys=True, ensure_ascii=False))
            if key in seen:
                continue
            seen.add(key)
            out.append((f"{rec['arm']} {rec['item']} t{t['turn']}", item["files"], CNT, ("curve", "chart"),
                        hatch_of(rec["arm"]), spec))
    return out


def tga_specs():
    """The hand-written TGA answers: tests/reference_specs.json (Set A) and eval/reference_b.json (Set B)."""
    out = []
    for path in (ROOT / "tests" / "reference_specs.json", HERE / "reference_b.json"):
        for rid, spec in json.loads(path.read_text(encoding="utf-8")).items():
            if rid.startswith("_") or not isinstance(spec, dict):
                continue
            hatch = "echarts" if rid.endswith("@echarts") else "code"
            files = spec["file"] if isinstance(spec["file"], list) else [spec["file"]]
            files = [f for f in files if "*" not in f]
            names = [Path(f).name for f in files]
            s = dict(spec, file=names if isinstance(spec["file"], list) else names[0])
            out.append((f"TGA {rid}", files, ROOT, ("curve",), hatch, s))
    return out


# =================================================================== checks
_INFO = {}


def info_for(files, root, inspect):
    key = (tuple(files), str(root), inspect)
    if key not in _INFO:
        inf = ss.data_info(files, root, inspect=inspect)
        if inspect:          # the TGA harness shows (and accepts) base file names
            inf["files"] = list(dict.fromkeys([Path(f).name for f in inf["files"]]))
        _INFO[key] = inf
    return _INFO[key]


def check_columns(cases):
    """Each enum value must resolve to exactly one column (chartkit.find_col on the frame)."""
    bad, n = [], 0
    done = set()
    for _, files, root, kinds, _, _ in cases:
        if tuple(files) in done or root != CNT:
            continue
        done.add(tuple(files))
        inf = info_for(files, root, False)
        for f in files:
            for p in sorted(glob.glob(str(root / f))):
                pv = chartkit.preview(p)
                for sh in pv["sheets"]:
                    try:
                        df = chartkit.load_frame({"file": [p], "sheets": sh["sheet"], "read": {}})
                    except Exception as e:  # noqa: BLE001
                        bad.append(f"{p} {sh['sheet']}: cannot load ({e})")
                        continue
                    for c in sh["columns"]:
                        for v in (c["name"], ss._base_name(c["name"]), c["col"]):
                            if not v:
                                continue
                            n += 1
                            assert v in inf["columns"], v
                            try:
                                hit = chartkit.find_col(df, v, "x")
                            except pk.PlotkitError as e:
                                bad.append(f"{Path(p).name}/{sh['sheet']}: {v!r} -> {e.message}")
                                continue
                            if hit != c["name"]:
                                bad.append(f"{Path(p).name}/{sh['sheet']}: {v!r} -> {hit!r}, not {c['name']!r}")
    return {"checked": n, "problems": bad}


def check_replay(cases):
    res = collections.defaultdict(lambda: {"n": 0, "raw_ok": 0, "canon_ok": 0})
    raw_reasons, canon_fail = collections.Counter(), []
    for label, files, root, kinds, hatch, spec in cases:
        inf = info_for(files, root, root == ROOT)
        sch = ss.build(inf, kinds, hatch)
        grp = label.split()[0]
        r = res[grp]
        r["n"] += 1
        e_raw = ss.best_alternative_errors(spec, sch)
        r["raw_ok"] += not e_raw
        for e in e_raw[:1]:
            raw_reasons[e.split(" was unexpected")[0][:110]] += 1
        e_can = ss.best_alternative_errors(canonical(spec), sch)
        r["canon_ok"] += not e_can
        if e_can:
            canon_fail.append({"case": label, "errors": e_can, "spec": canonical(spec)})
    return {"by_group": dict(res), "raw_reasons": raw_reasons.most_common(15), "canonical_failures": canon_fail}


def _norm_eq(a, b, is_chart):
    def n(s):
        try:
            d = chartkit.normalize(s) if is_chart else pk.normalize_spec(s)
        except pk.PlotkitError as e:
            return f"ERROR {e.message}"
        d = copy.deepcopy(d)
        d.pop("file", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    return n(a) == n(b)


def check_flat(cases):
    n = ok_rt = ok_valid = 0
    fails = []
    for label, files, root, kinds, hatch, spec in cases:
        spec = canonical(spec)
        inf = info_for(files, root, root == ROOT)
        fsch = ss.build(inf, kinds, hatch, profile="flat")
        n += 1
        flat = ss.spec_to_flat(spec, inf["columns"])
        errs = ss.validate(flat, fsch)
        ok_valid += not errs
        try:
            back = ss.flat_to_spec(flat)
            same = _norm_eq(spec, back, "chart" in spec)
        except ValueError as e:
            back, same = str(e), False
        ok_rt += same
        if errs or not same:
            fails.append({"case": label, "schema_errors": errs, "roundtrip_same": same, "spec": spec, "back": back})
    return {"n": n, "flat_valid": ok_valid, "roundtrip_same": ok_rt, "failures": fails}


def check_limits(cases):
    worst = {"optional": 0, "anyof": 0}
    ok = True
    sizes = []
    for _, files, root, kinds, hatch, _ in cases:
        inf = info_for(files, root, root == ROOT)
        lim = ss.limits(ss.build(inf, kinds, hatch, profile="flat"))
        ok &= lim["anthropic_ok"]
        worst = {k: max(worst[k], lim[k]) for k in worst}
        sizes.append(len(json.dumps(ss.build(inf, kinds, hatch), ensure_ascii=False)))
    return {"all_flat_within_anthropic_limits": ok, "worst": worst,
            "full_schema_bytes": {"min": min(sizes), "max": max(sizes)}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a = ap.parse_args()
    cases = dev_specs() + tga_specs()
    out = {"cases": len(cases), "columns": check_columns(cases), "replay": check_replay(cases),
           "flat": check_flat(cases), "limits": check_limits(cases)}
    p = HERE / "results" / "cd_selftest.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"cases: {out['cases']}")
    print(f"columns: {out['columns']['checked']} enum values, {len(out['columns']['problems'])} problems")
    for g, r in out["replay"]["by_group"].items():
        print(f"replay {g:6s}: {r['n']} specs, fit as written {r['raw_ok']}, fit after aliases -> canonical {r['canon_ok']}")
    f = out["flat"]
    print(f"flat: {f['n']} specs, valid {f['flat_valid']}, round trip identical {f['roundtrip_same']}")
    print(f"limits: {out['limits']}")
    print(f"details: {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
