"""Blind visual review: for each request, the six arms' plots in a shuffled order labelled A-F.

    python eval/review_sheets.py --run t0          -> eval/results/review/<run>/<request>.png + key.json
    python eval/review_sheets.py --run t0 --unblind -> eval/results/review_<run>.csv (grades joined to arms)

Grade each page in eval/results/review/<run>/grades.csv: request,label,verdict(yes|partial|no),defects
(defects: free words such as overlap, clipped, tofu, wrong-data, unreadable, missing-label). The key is
written to key.json and is not needed for grading.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="t0")
    ap.add_argument("--repeat", default="1")
    ap.add_argument("--unblind", action="store_true")
    a = ap.parse_args()
    out = HERE / "results" / "review" / a.run
    rows = [r for r in csv.DictReader(open(HERE / "results" / f"batch_{a.run}.csv", encoding="utf-8"))
            if r["repeat"] == a.repeat]
    if a.unblind:
        key = json.loads((out / "key.json").read_text(encoding="utf-8"))
        grades = list(csv.DictReader(open(out / "grades.csv", encoding="utf-8")))
        res = []
        for g in grades:
            arm = key[g["request"]][g["label"]]
            auto = next((r for r in rows if r["request"] == g["request"] and r["arm"] == arm), {})
            res.append({**g, "arm": arm, "pass_all": auto.get("pass_all"), "pass_ask": auto.get("pass_ask")})
        p = HERE / "results" / f"review_{a.run}.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0]))
            w.writeheader()
            w.writerows(res)
        print(f"{len(res)} grades -> {p.relative_to(ROOT)}")
        return

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
    from requests_b import REQUESTS
    import run_agent
    texts = {rid: t for rid, _, _, t in run_agent.read_prompts(ROOT / "tests" / "AGENT_TEST_PROMPTS.md")}
    texts.update({n.split("_")[0]: t for n, _, _, t in REQUESTS})
    out.mkdir(parents=True, exist_ok=True)
    key = {}
    by_req = {}
    for r in rows:
        by_req.setdefault(r["request"], []).append(r)
    for rid, rs in sorted(by_req.items()):
        rng = random.Random(f"{a.run}-{rid}")
        rs = sorted(rs, key=lambda r: r["arm"])
        rng.shuffle(rs)
        labels = "ABCDEF"[:len(rs)]
        key[rid] = {lab: r["arm"] for lab, r in zip(labels, rs)}
        fig, axs = plt.subplots(2, 3, figsize=(16, 8.6))
        fig.suptitle(f"{rid}: {texts.get(rid, '')}", fontsize=11, wrap=True)
        for ax, lab, r in zip(axs.flat, labels, rs):
            ax.axis("off")
            imgs = sorted((HERE / r["run_dir"] / "out").rglob("*.png")) if r["ok_run"] == "1" else []
            if imgs:
                ax.imshow(plt.imread(imgs[0]))
                more = f"  (+{len(imgs) - 1} more)" if len(imgs) > 1 else ""
            else:
                ax.text(0.5, 0.5, "no plot", ha="center", va="center", fontsize=14)
                more = ""
            ax.set_title(f"{lab}{more}", fontsize=12, loc="left")
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        fig.savefig(out / f"{rid}.png", dpi=90)
        plt.close(fig)
    (out / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    g = out / "grades.csv"
    if not g.exists():
        g.write_text("request,label,verdict,defects\n", encoding="utf-8")
    print(f"{len(by_req)} pages -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
