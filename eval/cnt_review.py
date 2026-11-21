"""Blind visual review of a CNT run: for each turn of repeat 1, one sheet with every arm's figure in a shuffled
order, labelled A, B, C, ...

    python eval/cnt_review.py --run sealed1            -> eval/results/review/cnt_<run>/<item>_t<turn>.png, key.json, turns.tsv
    python eval/cnt_review.py --run sealed1 --unblind  -> eval/results/review_cnt_<run>.csv (grades joined to arms)
    python eval/cnt_review.py --run sealed_review --sample 48   (a random sample of turns; --extra adds another run's arm)

Grades go in eval/results/review/cnt_<run>/grades.csv: sheet,label,verdict(yes|partial|no),defects.
turns.tsv gives the graders each sheet's request text (and, for a session, the earlier turns).
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--repeat", default="1")
    ap.add_argument("--unblind", action="store_true")
    ap.add_argument("--sample", type=int, help="grade only this many randomly chosen turns")
    a = ap.parse_args()
    out = HERE / "results" / "review" / f"cnt_{a.run}"
    rows = [r for r in csv.DictReader(open(HERE / "results" / f"cnt_{a.run}.csv", encoding="utf-8")) if r["repeat"] == a.repeat]
    if a.unblind:
        key = json.loads((out / "key.json").read_text(encoding="utf-8"))
        grades = list(csv.DictReader(open(out / "grades.csv", encoding="utf-8")))
        res = []
        for g in grades:
            arm = key[g["sheet"]][g["label"]]
            item, turn = g["sheet"].rsplit("_t", 1)
            auto = next((r for r in rows if r["item"] == item and r["turn"] == turn and r["arm"] == arm), {})
            res.append({**g, "arm": arm, "item": item, "turn": turn, "pass": auto.get("pass")})
        p = HERE / "results" / f"review_cnt_{a.run}.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0]))
            w.writeheader()
            w.writerows(res)
        print(len(res), "grades ->", p.relative_to(HERE.parent))
        return
    from PIL import Image, ImageDraw, ImageFont
    out.mkdir(parents=True, exist_ok=True)
    font = None
    for f in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(f).exists():
            font = ImageFont.truetype(f, 34)
            break
    rng = random.Random(5)
    by = {}
    for r in rows:
        by.setdefault((r["item"], r["turn"]), {})[r["arm"]] = r
    key, tsv = {}, []
    if a.sample and a.sample < len(by):
        keep = set(random.Random(11).sample(sorted(by), a.sample))
        by = {k: v for k, v in by.items() if k in keep}
    items = {}
    split = rows[0]["split"] if rows else "sealed"
    for it in json.loads((HERE / "cnt" / split / "requests.json").read_text(encoding="utf-8"))["items"]:
        items[it["id"]] = it
    for (item, turn), arms in sorted(by.items()):
        sheet = f"{item}_t{turn}"
        names = sorted(arms)
        rng.shuffle(names)
        panels = []
        for lab, arm in zip("ABCDEFGH", names):
            r = arms[arm]
            png = sorted((HERE / r["run_dir"] / "out" / f"t{turn}").glob("*.png")) if r["ok_run"] == "1" else []
            if png:
                im = Image.open(png[0]).convert("RGB")
                im.thumbnail((900, 640))
                more = len(png) - 1
            else:
                im = Image.new("RGB", (900, 640), "white")
                ImageDraw.Draw(im).text((300, 300), "no plot", fill="gray", font=font)
                more = 0
            panels.append((lab, im, more))
            key.setdefault(sheet, {})[lab] = arm
        W = 2 * 920
        H = ((len(panels) + 1) // 2) * 700
        canvas = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(canvas)
        for i, (lab, im, more) in enumerate(panels):
            x, y = (i % 2) * 920, (i // 2) * 700
            canvas.paste(im, (x + 10, y + 50))
            d.text((x + 10, y + 5), lab + (f"  (+{more} more)" if more else ""), fill="black", font=font)
        canvas.save(out / f"{sheet}.png")
        it = items[item]
        hist = " / ".join(f"[{i}] {t['text']}" for i, t in enumerate(it["turns"][: int(turn) - 1], 1))
        tsv.append(f"{sheet}\t{' '.join(it['files'])}\t{it['turns'][int(turn) - 1]['text']}\t{hist}")
    (out / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    (out / "turns.tsv").write_text("sheet\tfiles\trequest\tearlier turns\n" + "\n".join(tsv), encoding="utf-8")
    print(len(key), "sheets ->", out.relative_to(HERE.parent))


if __name__ == "__main__":
    sys.exit(main())
