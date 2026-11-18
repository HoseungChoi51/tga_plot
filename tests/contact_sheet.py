"""Put the matplotlib and ECharts images of every request side by side, for the visual check.

    python tests/contact_sheet.py                 arm 0 vs arm S images from results/out/  (after score.py runs)
    python tests/contact_sheet.py --reference     reference specs, both engines (run score.py --reference first)
    python tests/contact_sheet.py --png           also write PNG pages (6 requests each) next to the HTML

Writes results/contact_sheet.html (or results/contact_sheet_reference.html). Open it in a browser and
note every request where the change asked for is not visible.
"""
import argparse
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PROMPTS = ROOT / "tests" / "AGENT_TEST_PROMPTS.md"


def requests():
    """{"01": ("01_minimal", "request text"), ...} from AGENT_TEST_PROMPTS.md."""
    out, name, buf, inside = {}, None, [], False
    for line in PROMPTS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
        elif line.startswith("```text"):
            inside, buf = True, []
        elif line.startswith("```") and inside:
            inside = False
            out[name[:2]] = (name, "\n".join(buf))
        elif inside:
            buf.append(line)
    return out


def images(folder):
    return sorted(p for p in folder.glob("*.png")) if folder.exists() else []


def last_rows(arm):
    path = RESULTS / f"arm{arm}.csv"
    rows = {}
    if path.exists():
        with open(path, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                rows[r["request"].zfill(2)] = r
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--png", action="store_true")
    a = ap.parse_args()
    if a.reference:
        left, right = RESULTS / "reference" / "matplotlib", RESULTS / "reference" / "echarts"
        heads, out, rows = ("matplotlib", "ECharts"), RESULTS / "contact_sheet_reference.html", ({}, {})
    else:
        left, right = RESULTS / "out" / "0", RESULTS / "out" / "S"
        heads, out, rows = ("arm 0 (matplotlib)", "arm S (ECharts)"), RESULTS / "contact_sheet.html", (last_rows("0"), last_rows("S"))
    reqs = requests()
    parts = ["<!doctype html><meta charset='utf-8'><title>plotkit engines side by side</title>",
             "<style>body{font-family:sans-serif;margin:16px}td{vertical-align:top;padding:6px;border-top:1px solid #ccc}"
             "img{width:420px;display:block;margin-bottom:4px}pre{white-space:pre-wrap;width:260px;font-size:12px}"
             ".fail{color:#b00}</style>",
             f"<table><tr><th>request</th><th>{heads[0]}</th><th>{heads[1]}</th></tr>"]
    pages = []
    for r, (name, text) in reqs.items():
        cells = []
        for folder, rowset in ((left, rows[0]), (right, rows[1])):
            imgs = images(folder / r)
            row = rowset.get(r)
            mark = ""
            if row:
                mark = "<b>PASS</b>" if row["pass"] == "1" else f"<b class='fail'>FAIL</b> {html.escape(row['failed_checks'])}"
            cells.append(mark + "".join(f"<img src='{html.escape(p.relative_to(RESULTS).as_posix())}'>" for p in imgs[:3])
                         + ("" if imgs else "<i>no image</i>"))
            pages.append((r, folder.name, imgs[:1]))
        parts.append(f"<tr><td><b>{html.escape(name)}</b><pre>{html.escape(text)}</pre></td><td>{cells[0]}</td><td>{cells[1]}</td></tr>")
    parts.append("</table>")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ids = list(reqs)
        for page in range(0, len(ids), 6):
            chunk = ids[page:page + 6]
            fig, axs = plt.subplots(len(chunk), 2, figsize=(10, 3.6 * len(chunk)), squeeze=False)
            for i, r in enumerate(chunk):
                for j, folder in enumerate((left, right)):
                    ax = axs[i][j]
                    ax.axis("off")
                    imgs = images(folder / r)
                    if imgs:
                        ax.imshow(plt.imread(imgs[0]))
                    ax.set_title(f"{reqs[r][0]} - {heads[j]}", fontsize=9)
            fig.tight_layout()
            p = out.with_name(f"{out.stem}_{page // 6 + 1}.png")
            fig.savefig(p, dpi=110)
            plt.close(fig)
            print(f"wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
