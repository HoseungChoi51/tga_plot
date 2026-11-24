"""Checker sanity: specs known to be right (reference specs, Odin's earlier passing specs) must pass the
fact checks on both engines, and the fact verdict must agree with tests/score.py's spec verdict.

    python experiments/eval/validate_checker.py      -> eval/results/checker_validation.csv
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit/, tests/inputs, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))   # score.py
sys.path.insert(0, str(HERE))
import check  # noqa: E402
import paths  # noqa: E402
import facts  # noqa: E402
import score as spec_score  # noqa: E402

OUT = HERE / "results" / "validate"


def sources():
    ref = json.loads((REPO / "tests" / "reference_specs.json").read_text(encoding="utf-8"))
    for rid, s in ref.items():
        if rid.startswith("_"):
            continue
        yield "reference", rid, s
    refb = json.loads((HERE / "reference_b.json").read_text(encoding="utf-8"))
    for rid, s in refb.items():
        if not rid.startswith("_"):
            yield "reference_b", rid, s
    exp = json.loads((ROOT / "tests" / "expected_requests.json").read_text(encoding="utf-8"))
    for rid, e in exp.items():                   # negative control: the bare file, none of the asked changes
        if not rid.startswith("_"):
            yield "defaults", rid, {"file": e["file"]}
    for arm in "0S":
        p = ROOT / "results" / f"batch_{arm}.csv"
        if p.exists():
            for r in csv.DictReader(open(p, encoding="utf-8-sig")):
                if r["model"] == "odin" and r["repeat"] == "1" and r["spec"]:
                    yield f"odin_{arm}", r["request"], json.loads(r["spec"])


def main():
    E = json.loads((HERE / "expected_facts.json").read_text(encoding="utf-8"))
    rows = []
    for src, rid, spec in sources():
        only = None
        if "@" in rid:
            rid, only = rid.split("@")
        for eng in ("matplotlib", "echarts"):
            if only and eng != only:
                continue
            if ("code" in spec and eng == "echarts") or ("echarts" in spec and eng == "matplotlib"):
                continue
            s = dict(spec)
            f = s["file"]
            s["file"] = [str(paths.datapath(x)) for x in f] if isinstance(f, list) else str(paths.datapath(f))
            outdir = OUT / src / eng / rid
            if rid.startswith("B"):
                spec_ok, spec_why = True, []          # Set B has no spec-based checks
            else:
                spec_ok, spec_why, _ = spec_score.score(rid, dict(s), eng, outdir)
            s["output"] = {**s.get("output", {}), "dir": str(outdir)}
            try:
                _, figs = facts.plotkit_facts(s, eng, OUT / "dump.json")
                ok, res = check.run_checks(figs, E[rid])
                why = " | ".join(f"[{r['cat']}] {r['check']}: {r['why']}" for r in res if not r["ok"])
            except Exception as e:
                ok, why = False, f"error: {e!r}"
            rows.append({"source": src, "engine": eng, "request": rid, "spec_ok": int(spec_ok), "fact_ok": int(ok),
                         "fact_why": why, "spec_why": " | ".join(spec_why)})
            flag = "" if ok == spec_ok else "  <-- DISAGREE"
            if not ok or flag:
                print(f"{src:10s} {eng:10s} {rid} spec={int(spec_ok)} fact={int(ok)}{flag}  {why[:300]}")
    p = HERE / "results" / "checker_validation.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    agree = sum(r["spec_ok"] == r["fact_ok"] for r in rows)
    print(f"\n{len(rows)} runs, fact pass {sum(r['fact_ok'] for r in rows)}, agreement {agree}/{len(rows)}")


if __name__ == "__main__":
    main()
