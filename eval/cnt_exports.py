"""E4a: are the engines' exports fit for a journal or a slide? No model involved.

Every dev reference spec (eval/cnt_dev_refs.py) is drawn by both engines as a journal figure (3.5 x 2.6 in,
600 dpi, font size 8, PNG + PDF) and as a slide figure (10 x 5.6 in, font 16, PNG). Automatic checks:
  - PNG pixel size equals inches x dpi
  - PDF: vector (no raster images inside), every font embedded, page size in inches
  - the figure facts agree with the expectation (cnt_check), as in the main runs
Writes eval/results/cnt_exports.csv and pairs of PNGs (eval/results/exports/<id>/{a,b}.png, engines shuffled,
key in key.json) for a blind side-by-side review.

    python eval/cnt_exports.py
"""
import csv
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import cnt_check  # noqa: E402
import cnt_runs  # noqa: E402
from cnt_dev_refs import REFS  # noqa: E402

STYLES = {"journal": {"size": [3.5, 2.6], "dpi": 600, "font_size": 8, "output": {"format": ["png", "pdf"]}},
          "slide": {"size": [10, 5.6], "dpi": 150, "font_size": 16, "output": {"format": ["png"]}}}


def png_px(p):
    import struct
    with open(p, "rb") as fh:
        h = fh.read(24)
    return list(struct.unpack(">II", h[16:24])) if h[:8] == b"\x89PNG\r\n\x1a\n" else None


def pdf_info(p):
    out = {}
    info = subprocess.run(["pdfinfo", str(p)], capture_output=True, text=True).stdout
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info)
    out["page_in"] = [round(float(m.group(1)) / 72, 3), round(float(m.group(2)) / 72, 3)] if m else None
    imgs = subprocess.run(["pdfimages", "-list", str(p)], capture_output=True, text=True).stdout.strip().splitlines()[2:]
    out["images"] = len(imgs)
    fonts = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True).stdout.strip().splitlines()[2:]
    out["fonts"] = len(fonts)
    out["fonts_not_embedded"] = sum(1 for l in fonts if len(l.split()) >= 5 and l.split()[-5] == "no")
    out["font_names"] = sorted({l.split()[0] for l in fonts if l.split()})
    return out


def main():
    items = {f"{it['id']}.{i}": t["expect"] for it in json.loads((HERE / "cnt" / "dev" / "requests.json").read_text())["items"]
             for i, t in enumerate(it["turns"], 1)}
    root = HERE / "results" / "exports"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    work = root / "_work"
    work.mkdir()
    (work / "data").symlink_to(HERE / "cnt" / "data", target_is_directory=True)
    rng = random.Random(11)
    key = {}
    rows = []
    for k, spec in REFS.items():
        for style, st in STYLES.items():
            pngs = {}
            for eng in ("matplotlib", "echarts"):
                sp = {**spec, **{kk: v for kk, v in st.items() if kk != "output"}, "output": {**st["output"], "name": "fig"}}
                tag = f"{k.replace('.', '_')}_{style}_{eng}"
                res, facts, dt = cnt_runs.draw_spec(sp, eng, work, tag)
                row = {"ref": k, "style": style, "engine": eng, "ok": int(bool(res.get("ok"))), "draw_s": round(dt, 2),
                       "error": "" if res.get("ok") else res.get("error", "")[:200]}
                if res.get("ok"):
                    chk = cnt_check.check(items[k], facts, res)
                    row["pass"] = int(bool(chk["pass"]))
                    row["failed"] = " | ".join(chk["failed"])[:300]
                    outdir = work / "out" / f"t{tag}"
                    png = next(outdir.glob("*.png"), None)
                    want = [round(st["size"][0] * st["dpi"]), round(st["size"][1] * st["dpi"])]
                    if png:
                        px = png_px(png)
                        row["png_px"] = px
                        row["png_px_ok"] = int(px is not None and all(abs(a - b) <= 2 for a, b in zip(px, want)))
                        pngs[eng] = png
                    pdf = next(outdir.glob("*.pdf"), None)
                    if pdf:
                        pi = pdf_info(pdf)
                        row.update({"pdf_page_in": pi["page_in"], "pdf_images": pi["images"], "pdf_fonts": pi["fonts"],
                                    "pdf_fonts_not_embedded": pi["fonts_not_embedded"], "pdf_font_names": " ".join(pi["font_names"])[:120],
                                    "pdf_vector": int(pi["images"] == 0),
                                    "pdf_size_ok": int(pi["page_in"] is not None and all(abs(a - b) <= 0.02 for a, b in zip(pi["page_in"], st["size"])))})
                rows.append(row)
                print(f"{k:8} {style:8} {eng:10} ok={row['ok']} pass={row.get('pass')} px={row.get('png_px')} "
                      f"vector={row.get('pdf_vector')} unembedded={row.get('pdf_fonts_not_embedded')} {row['error'][:80]}", flush=True)
            if len(pngs) == 2:
                d = root / f"{k}_{style}"
                d.mkdir()
                order = ["matplotlib", "echarts"]
                rng.shuffle(order)
                for lab, eng in zip("ab", order):
                    shutil.copy(pngs[eng], d / f"{lab}.png")
                key[f"{k}_{style}"] = {"a": order[0], "b": order[1]}
    (root / "key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    keys = sorted({k for r in rows for k in r})
    with open(HERE / "results" / "cnt_exports.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
