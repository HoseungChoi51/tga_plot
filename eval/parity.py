"""Engine parity: draw the same specs with matplotlib and ECharts and compare what was drawn (figure facts).

    python eval/parity.py      -> eval/results/parity.csv (one row per difference) + parity_summary.json
Also times each draw (PNG; and PDF for a few specs) for the latency comparison.
"""
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import check  # noqa: E402
import facts  # noqa: E402

OUT = HERE / "results" / "parity"

PROBES = {   # specs aimed at suspected differences
    "probe_linestyle_dash_alias": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "y2": {"linestyle": "--"}},
    "probe_linestyle_korean": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "y2": {"linestyle": "점선"}},
    "probe_linestyle_dotted": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "y2": {"linestyle": "dotted"}},
    "probe_residue_beyond_xmax": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "x": {"max": 700}},
    "probe_auto_ticks_small_fig": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "size": [3.4, 2.6], "font_size": 8},
    "probe_tick_inout": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "tick_direction": "inout"},
    "probe_legend_best": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "legend": "best"},
    "probe_scatter_style": {"file": "tests/inputs/TGA.xlsx", "sheets": 1, "y1": {"style": "scatter"},
                            "y2": {"style": "line+marker"}},
}


def specs():
    for p in sorted((ROOT / "gallery" / "specs").glob("*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        if "code" in s or "echarts" in s:
            continue
        f = s["file"]
        s["file"] = [str(ROOT / "gallery" / x) for x in f] if isinstance(f, list) else str(ROOT / "gallery" / f)
        yield f"gallery_{p.stem[:2]}", s
    ref = json.loads((ROOT / "tests" / "reference_specs.json").read_text(encoding="utf-8"))
    for rid, s in ref.items():
        if rid.startswith("_") or "@" in rid or "code" in s or "echarts" in s:
            continue
        s = dict(s, file=str(ROOT / s["file"]))
        yield f"ref_{rid}", s
    refb = json.loads((HERE / "reference_b.json").read_text(encoding="utf-8"))
    for rid, s in refb.items():
        if rid.startswith("_") or "@" in rid:
            continue
        f = s["file"]
        s = dict(s, file=[str(ROOT / x) for x in f] if isinstance(f, list) else str(ROOT / f))
        yield f"refb_{rid}", s
    for k, s in PROBES.items():
        yield k, dict(s, file=str(ROOT / s["file"]))


def rel(a, b, span):
    return abs((a or 0) - (b or 0)) / (span or 1)


def compare(sid, fm, fe):
    """Differences between two lists of figure facts (same spec)."""
    diffs = []
    add = lambda field, a, b, kind: diffs.append({"spec": sid, "field": field, "matplotlib": a, "echarts": b, "kind": kind})  # noqa: E731
    if len(fm) != len(fe):
        add("figures", len(fm), len(fe), "structure")
        return diffs
    for i, (m, e) in enumerate(zip(fm, fe)):
        pre = f"fig{i}."
        for k in ("size_in",):
            if any(abs(a - b) > 0.01 for a, b in zip(m[k], e[k])):
                add(pre + k, m[k], e[k], "size")
        pm = [x["px"] for x in m["files"] if x.get("px")]
        pe = [x["px"] for x in e["files"] if x.get("px")]
        if pm != pe:
            add(pre + "png_px", pm, pe, "size")
        tm, te = m.get("title"), e.get("title")
        if bool(tm) != bool(te) or (tm and (tm["text"] != te["text"] or abs(tm["size"] - te["size"]) > 0.3
                                            or not check.color_ok(te["color"], tm["color"]))):
            add(pre + "title", tm, te, "text")
        for pi, (a, b) in enumerate(zip(m["panels"], e["panels"])):
            pp = f"{pre}p{pi}."
            for ax in ("x", "y1", "y2"):
                A, B = a.get(ax), b.get(ax)
                if bool(A) != bool(B):
                    add(pp + ax, bool(A), bool(B), "structure")
                    continue
                if not A:
                    continue
                span = abs(A["max"] - A["min"])
                if rel(A["min"], B["min"], span) > 0.005 or rel(A["max"], B["max"], span) > 0.005:
                    add(pp + ax + ".range", [A["min"], A["max"]], [B["min"], B["max"]], "axis range")
                ta = [round(t, 6) for t in A["ticks"]]
                tb = [round(t, 6) for t in B["ticks"] if A["min"] - 1e-9 <= t <= A["max"] + 1e-9]
                if A["scale"] == "log":
                    tb = [t for t in tb if any(abs(t - x) < 1e-9 * max(1, abs(x)) for x in ta)] if set(tb) - set(ta) else tb
                if ta != tb:
                    add(pp + ax + ".ticks", ta, [round(t, 6) for t in B["ticks"]], "ticks")
                for k in ("scale", "inverted", "label", "tick_direction"):
                    if A[k] != B[k]:
                        add(pp + ax + "." + k, A[k], B[k], "axis style")
                for k in ("label_size", "tick_size"):
                    if A[k] is not None and B[k] is not None and abs(A[k] - B[k]) > 0.3:
                        add(pp + ax + "." + k, A[k], B[k], "axis style")
                for k in ("label_color", "tick_color"):
                    if A[k] and B[k] and not check.color_ok(B[k], A[k]):
                        add(pp + ax + "." + k, A[k], B[k], "axis style")
            if len(a["lines"]) != len(b["lines"]):
                add(pp + "lines", len(a["lines"]), len(b["lines"]), "structure")
            for li, (la, lb) in enumerate(zip(a["lines"], b["lines"])):
                for k in ("axis", "kind", "style", "marker"):
                    if la[k] != lb[k]:
                        add(f"{pp}line{li}.{k}", la[k], lb[k], "line style")
                if not check.color_ok(lb["color"], la["color"]):
                    add(f"{pp}line{li}.color", la["color"], lb["color"], "line style")
                if la["kind"] == "line" and abs(la["width"] - lb["width"]) > 0.2:
                    add(f"{pp}line{li}.width", la["width"], lb["width"], "line style")
            for k in ("spans", "vlines", "hlines"):
                if len(a[k]) != len(b[k]):
                    add(pp + k, len(a[k]), len(b[k]), "annotation")
            if a["grid"] != b["grid"]:
                add(pp + "grid", a["grid"], b["grid"], "axis style")
        # texts: same strings? same x?
        sm = Counter(t["text"].strip() for t in m["texts"])
        se = Counter(t["text"].strip() for t in e["texts"])
        if sm != se:
            add(pre + "texts", sorted((sm - se).elements()), sorted((se - sm).elements()), "annotation text")
        xa = m["panels"][0]["x"] if m["panels"] else None
        for t in e["texts"]:
            if xa and t["x"] is not None and not (xa["min"] - 1e-6 <= t["x"] <= xa["max"] + 1e-6) and t["text"].strip() in sm:
                pass
            if xa and t["x"] is not None and not (xa["min"] - 0.02 * (xa["max"] - xa["min"]) <= t["x"] <= xa["max"] + 0.02 * (xa["max"] - xa["min"])):
                add(pre + "text_outside_plot", None, t["text"], "annotation text")
        lm, le = m["legend"], e["legend"]
        if lm["shown"] != le["shown"] or lm.get("where") != le.get("where") or lm.get("entries") != le.get("entries"):
            add(pre + "legend", {k: lm.get(k) for k in ("shown", "where", "entries")},
                {k: le.get(k) for k in ("shown", "where", "entries")}, "legend")
    return diffs


def main():
    rows, timing, n = [], [], 0
    for sid, s in specs():
        n += 1
        out = {}
        for eng in ("matplotlib", "echarts"):
            s2 = dict(s, output={**s.get("output", {}), "dir": str(OUT / eng / sid)})
            t0 = time.perf_counter()
            try:
                _, figs = facts.plotkit_facts(s2, eng, OUT / f"dump_{sid}.json")
                out[eng] = figs
            except Exception as e:
                out[eng] = None
                rows.append({"spec": sid, "field": "error", "matplotlib": "" if eng == "echarts" else repr(e),
                             "echarts": repr(e) if eng == "echarts" else "", "kind": "error"})
            timing.append({"spec": sid, "engine": eng, "seconds": round(time.perf_counter() - t0, 3),
                           "figures": len(out[eng] or []), "formats": ",".join(sorted({x["format"] for f in out[eng] or [] for x in f["files"]}))})
        if out["matplotlib"] is not None and out["echarts"] is not None:
            rows += compare(sid, out["matplotlib"], out["echarts"])
    OUT.mkdir(parents=True, exist_ok=True)
    with open(HERE / "results" / "parity.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["spec", "kind", "field", "matplotlib", "echarts"])
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(r[k], ensure_ascii=False) if not isinstance(r[k], str) else r[k] for k in w.fieldnames})
    with open(HERE / "results" / "latency.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(timing[0]))
        w.writeheader()
        w.writerows(timing)
    kinds = Counter(r["kind"] for r in rows)
    specs_with = len({r["spec"] for r in rows})
    summ = {"specs": n, "specs_with_differences": specs_with, "differences_by_kind": dict(kinds)}
    (HERE / "results" / "parity_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
