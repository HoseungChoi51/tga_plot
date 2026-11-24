"""Re-check a CNT run from its records with the current checker (no model calls) and rewrite its CSV.

    python experiments/eval/cnt_rescore.py --name dev_a
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))      # the library
sys.path.insert(0, str(HERE.parent))             # experiments/
sys.path.insert(0, str(HERE))
import cnt_check  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
a = ap.parse_args()
path = HERE / "results" / f"cnt_{a.name}.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))
fields = list(rows[0])
cache, changed = {}, 0
items = {}
for split in ("dev", "sealed"):
    p = HERE / "cnt" / split / "requests.json"
    if p.exists():
        items.update({it["id"]: it for it in json.loads(p.read_text(encoding="utf-8"))["items"]})
for r in rows:
    rd = HERE / r["run_dir"]
    if rd not in cache:
        cache[rd] = json.loads((rd / "record.json").read_text(encoding="utf-8"))
    rec = cache[rd]
    t = rec["turns"][int(r["turn"]) - 1]
    exp = items[r["item"]]["turns"][int(r["turn"]) - 1]["expect"]
    chk = cnt_check.check(exp, t["facts"], t["result"], t["spec"] if isinstance(t["spec"], dict) else None)
    new = {"pass": int(bool(chk["pass"])), "n_checks": chk["n_checks"], "n_failed": chk["n_failed"],
           "failed": " | ".join(chk["failed"])[:600], "unchecked": " | ".join(chk.get("unchecked", []))[:300]}
    if str(new["pass"]) != str(r["pass"]):
        changed += 1
    r.update(new)
    t["check"] = chk
for rd, rec in cache.items():
    (rd / "record.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
with open(path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} turns re-checked, {changed} changed -> {path.relative_to(HERE.parent)}")
