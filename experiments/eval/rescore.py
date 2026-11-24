"""Re-check finished runs with the current checker and expectations, without calling the model again.

    python experiments/eval/rescore.py --name sx      -> rewrites the pass columns of eval/results/batch_sx.csv (backup kept)
Uses each run's record.json (it holds the figure facts).
"""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    E = json.loads((HERE / "expected_facts.json").read_text(encoding="utf-8"))
    path = HERE / "results" / f"batch_{a.name}.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    changed = 0
    for r in rows:
        rec_p = HERE / r["run_dir"] / "record.json"
        if not rec_p.exists():
            continue
        rec = json.loads(rec_p.read_text(encoding="utf-8"))
        if rec["ok_run"]:
            ok, res = check.run_checks(rec["figures"], E[r["request"]])
        else:
            ok, res = False, [{"check": "run", "cat": "data", "ok": False, "why": "no plot after retries"}]
        cats = lambda cs: all(x["ok"] for x in res if x["cat"] in cs)  # noqa: E731
        new = {"pass_all": str(int(ok)), "pass_ask": str(int(rec["ok_run"] and cats(("data", "ask")))),
               "pass_data": str(int(rec["ok_run"] and cats(("data",)))),
               "pass_conv": "" if not any(x["cat"] == "conv" for x in res) else str(int(rec["ok_run"] and cats(("conv",)))),
               "n_failed": str(sum(not x["ok"] for x in res)),
               "first_try": str(int(ok and len(rec["calls"]) == 1)),
               "failed": " | ".join(f"[{x['cat']}] {x['check']}: {x['why']}" for x in res if not x["ok"])[:1500]}
        if any(r[k] != v for k, v in new.items()):
            changed += 1
        r.update(new)
    shutil.copy2(path, path.with_suffix(".csv.bak"))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows, {changed} changed -> {path.name} (backup .csv.bak)")


if __name__ == "__main__":
    main()
