"""Render saved specs again without the model, e.g. on the Windows PC for the font and path check.

    python experiments/tests/render_all.py --engine echarts                   specs the model wrote (results/specs/*.json)
    python experiments/tests/render_all.py --engine echarts --reference       the hand-written reference specs
    python experiments/tests/render_all.py --engine echarts --out "C:/Users/홍길동/Documents/tga plot/out"

Each request is scored as in score.py. Then open the images and check the Korean text.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # experiments/
REPO = ROOT.parent                                     # the library
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT / "tests"))
from plotkit import core as plotkit  # noqa: E402
import score  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", choices=plotkit.ENGINES, default="echarts")
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--arm", default="S", help="which saved specs: results/specs/<arm>_*.json (default S)")
    ap.add_argument("--out", help="output folder (default results/render/<engine>)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    out = Path(a.out) if a.out else ROOT / "results" / "render" / a.engine
    if a.reference:
        specs = {r: score.REFERENCE.get(f"{r}@{a.engine}", score.REFERENCE[r])
                 for r in score.EXPECTED if not r.startswith("_")}
    else:
        specs = {p.stem.split("_", 1)[1]: json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted((ROOT / "results" / "specs").glob(f"{a.arm}_*.json"))}
        if not specs:
            sys.exit(f"no specs in results/specs/{a.arm}_*.json; use --reference or run score.py first")
    fails = 0
    for r, spec in specs.items():
        spec = dict(spec)
        f = spec.get("file")
        if isinstance(f, str) and not Path(f).is_absolute():      # specs from Pi name files from the repo root
            spec["file"] = str(REPO / f) if (REPO / f).exists() else str(REPO / "tests" / "inputs" / Path(f).name)
        t0 = time.time()
        ok, why, res = score.score(r, spec, a.engine, out / r)
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {r}  {time.time() - t0:5.1f}s  " + ("; ".join(why) if why else
              ", ".join(Path(s).name for p in res["plots"] for s in p["saved"])))
    print(f"\nimages in {out}")
    print("ALL PASSED" if not fails else f"{fails} FAILED")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
