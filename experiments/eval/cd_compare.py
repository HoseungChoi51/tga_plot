"""Constrained decoding vs free decoding: paired comparison of the arms of one or more runs.

    python experiments/eval/cd_compare.py eval/results/cnt_cd1.csv                  # CNT harness (one row per turn)
    python experiments/eval/cd_compare.py eval/results/batch_cd_sx.csv              # TGA harness (one row per request)
    python experiments/eval/cd_compare.py eval/results/cnt_cd1.csv --by kind --list # by chart kind; list the pairs that differ

For every arm X with constrained variants (X+cd, X+cdflat) in the file, the rows are paired on
(item, turn, repeat) and only complete pairs are compared. Reported per arm:
  pass        share of turns whose figure passed every check; 95% CI from a bootstrap over items (turns of one item,
              its repeats and session turns are not independent, so whole items are resampled)
  Δ pass      paired difference to the free arm with its bootstrap CI, and McNemar's exact test on the discordant
              pairs (b = only the constrained arm passed, c = only the free arm passed)
  first try   passed with one model call;  retry  needed more than one call;  no plot  nothing drawn after retries
  fits schema the arm's FIRST reply fits its schema as written (for a free arm: how often the grammar would have
              changed its reply at all)
  llm s, out tok   median model time and output tokens per turn (all calls)
Writes the table also as JSON next to the CSV (<name>_cd_compare.json).
"""
import argparse
import collections
import csv
import json
import math
import random
import statistics
import sys
from pathlib import Path


def load(paths):
    rows = []
    for p in paths:
        for r in csv.DictReader(open(p, encoding="utf-8")):
            r["_file"] = Path(p).stem
            rows.append(r)
    if not rows:
        sys.exit("no rows")
    cnt = "item" in rows[0]
    for r in rows:
        r["_item"] = r["item"] if cnt else r["request"]
        r["_turn"] = r.get("turn", "1") if cnt else "1"
        r["_pass"] = int(r["pass"] == "1") if cnt else int(r["pass_all"] == "1")
        r["_key"] = (r["_item"], r["_turn"], r["repeat"])
        r["_ok"] = r.get("ok_run") == "1"
        r["_calls"] = int(r.get("model_calls") or 0)
        r["_first"] = int(r["_pass"] and r["_calls"] == 1)
    if cnt:
        rows = [r for r in rows if r["pass"] != ""]          # ungraded turns
    return rows, cnt


def med(xs):
    xs = [float(x) for x in xs if x not in ("", None)]
    return round(statistics.median(xs), 2) if xs else None


def pct(xs):
    return round(100 * sum(xs) / len(xs), 1) if xs else None


def boot(items_vals, stat, n=2000, seed=7):
    """95% CI of stat over a bootstrap of items. items_vals: {item: [values...]}."""
    rnd = random.Random(seed)
    keys = list(items_vals)
    if not keys:
        return None
    out = []
    for _ in range(n):
        sample = [v for k in (rnd.choice(keys) for _ in keys) for v in items_vals[k]]
        out.append(stat(sample))
    out.sort()
    return [round(out[int(0.025 * n)], 1), round(out[int(0.975 * n) - 1], 1)]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, 2 * p), 4)


def arm_stats(rows):
    by_item = collections.defaultdict(list)
    for r in rows:
        by_item[r["_item"]].append(r["_pass"])
    sch = [int(r["schema_ok_first"]) for r in rows if r.get("schema_ok_first") not in ("", None)]
    return {"n": len(rows), "pass": pct([r["_pass"] for r in rows]), "ci": boot(by_item, lambda v: 100 * sum(v) / len(v)),
            "first_try": pct([r["_first"] for r in rows]), "retry": pct([int(r["_calls"] > 1) for r in rows]),
            "no_plot": pct([int(not r["_ok"]) for r in rows]), "fits_schema": pct(sch),
            "llm_s": med(r.get("llm_s") or r.get("seconds") for r in rows),
            "out_tok": med(r.get("output_tokens") for r in rows)}


def paired(free, con):
    f = {r["_key"]: r for r in free}
    c = {r["_key"]: r for r in con}
    keys = sorted(set(f) & set(c))
    b = sum(1 for k in keys if c[k]["_pass"] and not f[k]["_pass"])
    cc = sum(1 for k in keys if f[k]["_pass"] and not c[k]["_pass"])
    diffs = collections.defaultdict(list)
    for k in keys:
        diffs[k[0]].append(c[k]["_pass"] - f[k]["_pass"])
    d = round(100 * sum(sum(v) for v in diffs.values()) / max(1, len(keys)), 1)
    return {"pairs": len(keys), "delta": d, "ci": boot(diffs, lambda v: 100 * sum(v) / len(v)),
            "only_cd_passed": b, "only_free_passed": cc, "mcnemar_p": mcnemar(b, cc),
            "differ": [{"item": k[0], "turn": k[1], "repeat": k[2], "cd_passed": c[k]["_pass"],
                        "cd_run": c[k].get("run_dir"), "free_run": f[k].get("run_dir"),
                        "cd_failed": (c[k].get("failed") or c[k].get("error") or "")[:160],
                        "free_failed": (f[k].get("failed") or f[k].get("error") or "")[:160]}
                       for k in keys if c[k]["_pass"] != f[k]["_pass"]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--by", help="also split by this column, e.g. kind, type, group, set")
    ap.add_argument("--list", action="store_true", help="list the pairs where the two arms differ")
    a = ap.parse_args()
    rows, cnt = load(a.csv)
    arms = sorted({r["arm"] for r in rows})
    bases = sorted({x.split("+")[0] for x in arms})
    out = {"files": a.csv, "arms": {}, "paired": {}}
    hdr = f"{'arm':16s} {'n':>5s} {'pass':>6s} {'95% CI':>13s} {'1st try':>7s} {'retry':>6s} {'noplot':>6s} {'fits':>6s} {'llm s':>6s} {'out tok':>7s}"
    print(hdr)
    for arm in arms:
        st = arm_stats([r for r in rows if r["arm"] == arm])
        out["arms"][arm] = st
        ci = f"[{st['ci'][0]}, {st['ci'][1]}]" if st["ci"] else ""
        print(f"{arm:16s} {st['n']:5d} {st['pass']:6.1f} {ci:>13s} {st['first_try']:7.1f} {st['retry']:6.1f} "
              f"{st['no_plot']:6.1f} {('' if st['fits_schema'] is None else st['fits_schema']):>6} {st['llm_s'] or '':>6} "
              f"{st['out_tok'] or '':>7}")
    print()
    for base in bases:
        free = [r for r in rows if r["arm"] == base]
        for arm in [x for x in arms if x.startswith(base + "+")]:
            if not free:
                print(f"{arm}: no free {base} rows to pair with")
                continue
            p = paired(free, [r for r in rows if r["arm"] == arm])
            out["paired"][f"{arm} vs {base}"] = p
            ci = f"[{p['ci'][0]}, {p['ci'][1]}]" if p["ci"] else ""
            print(f"{arm} vs {base}: {p['pairs']} pairs, Δ pass {p['delta']:+.1f} pts {ci}, "
                  f"only constrained passed {p['only_cd_passed']}, only free passed {p['only_free_passed']}, "
                  f"McNemar p = {p['mcnemar_p']}")
            if a.by:
                groups = sorted({r.get(a.by, "") for r in free})
                for g in groups:
                    pg = paired([r for r in free if r.get(a.by, "") == g],
                                [r for r in rows if r["arm"] == arm and r.get(a.by, "") == g])
                    if pg["pairs"]:
                        print(f"    {a.by}={g or '-':14s} {pg['pairs']:4d} pairs  Δ {pg['delta']:+6.1f}  "
                              f"(+{pg['only_cd_passed']} / -{pg['only_free_passed']})")
            if a.list:
                for d in p["differ"]:
                    tag = "CD only " if d["cd_passed"] else "free only"
                    print(f"    {tag} {d['item']} t{d['turn']} r{d['repeat']}  "
                          f"{'free: ' + d['free_failed'] if d['cd_passed'] else 'cd: ' + d['cd_failed']}")
                    print(f"             {d['cd_run']}  |  {d['free_run']}")
    dest = Path(a.csv[0]).with_name(Path(a.csv[0]).stem + "_cd_compare.json")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {dest}")


if __name__ == "__main__":
    main()
