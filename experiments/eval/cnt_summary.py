"""Aggregates of the sealed CNT runs (E2), per serving and arm: checker pass with an item-level bootstrap, silent failures,
hatch routes, retries and turn times. Reads only the result CSVs.

    python experiments/eval/cnt_summary.py                     -> tables on stdout, eval/results/cnt_summary.json
    python experiments/eval/cnt_summary.py --runs sealed,sealed_oc
"""
import argparse
import csv
import json
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"


def load(run):
    p = RES / f"cnt_{run}.csv"
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def by_item(rows):
    out = {}
    for r in rows:
        if r["pass"] in ("0", "1"):
            out.setdefault(r["item"], []).append(int(r["pass"]))
    return out


def boot(items_a, items_b=None, n=2000, seed=7):
    """Mean turn pass (or the paired difference a - b) with a 95% interval, resampling items."""
    keys = sorted(set(items_a) & set(items_b)) if items_b is not None else sorted(items_a)
    rng = random.Random(seed)

    def stat(ks):
        a = [v for k in ks for v in items_a[k]]
        if items_b is None:
            return sum(a) / len(a)
        b = [v for k in ks for v in items_b[k]]
        return sum(a) / len(a) - sum(b) / len(b)
    est = stat(keys)
    sims = sorted(stat([rng.choice(keys) for _ in keys]) for _ in range(n))
    return round(100 * est, 1), round(100 * sims[int(0.025 * n)], 1), round(100 * sims[int(0.975 * n)], 1)


def arm_stats(rows):
    graded = [r for r in rows if r["pass"] in ("0", "1")]
    n = len(rows)
    routes = {}
    for r in rows:
        routes[r["route"]] = routes.get(r["route"], 0) + 1
    drawing = sum(1 for r in rows if "code" in r["route"].split("+"))
    data_code = sum(1 for r in rows if "data_code" in r["route"].split("+"))
    silent = sum(1 for r in rows if r["ok_run"] == "1" and r["pass"] == "0" and r["unsupported"] in ("", "0"))
    flagged = sum(1 for r in rows if r["unsupported"] not in ("", "0"))
    nodraw = sum(1 for r in rows if r["ok_run"] != "1")
    kinds = {}
    for r in graded:
        kinds.setdefault(r["kind"] or "?", []).append(int(r["pass"]))
    types = {}
    for r in graded:
        key = r["type"] if r["type"] != "session" else ("session t1" if r["turn"] == "1" else "session t2+")
        types.setdefault(key, []).append(int(r["pass"]))
    reps = {}
    for r in graded:
        reps.setdefault(r["repeat"], []).append(int(r["pass"]))
    f = lambda k: [float(r[k]) for r in rows if r.get(k) not in (None, "")]  # noqa: E731
    est, lo, hi = boot(by_item(rows))
    return {"turns": n, "graded": len(graded), "pass": est, "ci": [lo, hi],
            "by_kind": {k: [round(100 * sum(v) / len(v), 1), len(v)] for k, v in sorted(kinds.items())},
            "by_type": {k: [round(100 * sum(v) / len(v), 1), len(v)] for k, v in sorted(types.items())},
            "by_repeat": {k: round(100 * sum(v) / len(v), 1) for k, v in sorted(reps.items())},
            "no_plot": round(100 * nodraw / n, 1), "silent": round(100 * silent / n, 1),
            "flagged_unsupported": round(100 * flagged / n, 1),
            "drawing_hatch": round(100 * drawing / n, 1), "data_code": round(100 * data_code / n, 1),
            "routes": {k: round(100 * v / n, 1) for k, v in sorted(routes.items(), key=lambda kv: -kv[1])},
            "retry_turns": round(100 * sum(1 for r in rows if int(r["model_calls"] or 0) > 1) / n, 1),
            "turn_s": [round(pct(f("turn_s"), q), 1) for q in (0.5, 0.9)],
            "llm_s": [round(pct(f("llm_s"), q), 1) for q in (0.5, 0.9)],
            "output_tokens_p50": pct(f("output_tokens"), 0.5)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="sealed,sealed_oc")
    a = ap.parse_args()
    out = {}
    for run in a.runs.split(","):
        rows = load(run)
        if not rows:
            continue
        arms = sorted({r["arm"] for r in rows})
        res = {arm: arm_stats([r for r in rows if r["arm"] == arm]) for arm in arms}
        items = {arm: by_item([r for r in rows if r["arm"] == arm]) for arm in arms}
        pairs = {}
        for x, y in [("P-ec", "P-mpl"), ("P-ec", "P-hyb"), ("P-hyb", "P-mpl"), ("P-mpl", "R-mpl"), ("P-ec", "R-mpl"),
                     ("P-hyb", "R-mpl")]:
            if x in items and y in items:
                pairs[f"{x} - {y}"] = boot(items[x], items[y])
        out[run] = {"arms": res, "paired": pairs}
        print(f"\n== {run}")
        print(f"{'arm':7} {'turns':>5} {'pass':>6} {'95% CI':>13} {'no plot':>8} {'silent':>7} {'flagged':>8} {'draw-hatch':>10}"
              f" {'data_code':>9} {'retry':>6} {'turn p50/p90':>13} {'llm p50/p90':>12}")
        for arm, s in res.items():
            print(f"{arm:7} {s['turns']:5} {s['pass']:6} {str(s['ci']):>13} {s['no_plot']:8} {s['silent']:7} "
                  f"{s['flagged_unsupported']:8} {s['drawing_hatch']:10} {s['data_code']:9} {s['retry_turns']:6} "
                  f"{str(s['turn_s']):>13} {str(s['llm_s']):>12}")
        for arm, s in res.items():
            print(f"  {arm} by type {s['by_type']}  by repeat {s['by_repeat']}")
            print(f"  {arm} by kind {s['by_kind']}")
        for k, v in pairs.items():
            print(f"  {k}: {v[0]:+.1f} points [{v[1]:+.1f}, {v[2]:+.1f}]")
    (RES / "cnt_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
