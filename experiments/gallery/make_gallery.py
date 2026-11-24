"""A gallery of plots drawn only from specs, on made-up data, with both engines.

    python experiments/gallery/make_gallery.py               # data, every spec, both engines -> gallery/index.html
    python experiments/gallery/make_gallery.py --only 03,24  # redraw a few
    python experiments/gallery/make_gallery.py --pages       # also gallery/pages_N.png (6 specs per page) for a quick look

Writes the made-up data to gallery/data/, each spec to gallery/specs/NN_name.json (exactly as shown on
the page) and the plots to gallery/out/<engine>/NN/. The script only adds "output.dir" and makes the
file paths absolute before drawing; everything else on the page is the spec plotkit received.
"""
import argparse
import copy
import csv
import html
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy.special import erf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit/, tests/inputs, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
from plotkit import core as plotkit  # noqa: E402

DATA, SPECS, OUT = HERE / "data", HERE / "specs", HERE / "out"
ENGINES = ("matplotlib", "echarts")
rng = np.random.default_rng(7)


# =================================================================== made-up data
def tga(steps, T):
    """Weight (%) and DTG (%/°C) for mass-loss steps [(loss %, centre °C, width °C), ...]."""
    W = 100.0 - sum(a * 0.5 * (1 + erf((T - c) / (w * np.sqrt(2)))) for a, c, w in steps)
    D = np.gradient(W, T)
    return W + rng.normal(0, 0.01, T.size), D + rng.normal(0, 0.0008, T.size)


def gauss(T, c, w):
    return np.exp(-0.5 * ((T - c) / w) ** 2)


def r(v, n=5):
    return float(f"{v:.{n}g}")


def write_csv(path, header, cols, sep=",", decimal="."):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write(sep.join(header) + "\n")
        for row in zip(*cols):
            fh.write(sep.join(str(r(v)).replace(".", decimal) for v in row) + "\n")


def write_xlsx(path, sheets, header):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, cols in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(header)
        for row in zip(*cols):
            ws.append([r(v) for v in row])
    wb.save(path)


def make_data(dest=None):
    dest = Path(dest) if dest else DATA
    dest.mkdir(parents=True, exist_ok=True)
    head = ["Time (min)", "Temperature (°C)", "Weight (%)", "Deriv. Weight (%/°C)"]

    T = np.arange(30.0, 900.1, 1.0)
    t = (T - 30) / 10
    polymers = {"PE": [(0.4, 90, 15), (98.6, 472, 16)],                 # one clean step, ~1 % char
                "PVC": [(58, 300, 22), (30, 455, 25)],                  # HCl first, then the backbone
                "PET": [(0.5, 95, 15), (82.5, 432, 19)]}                # ~17 % char
    write_xlsx(dest / "polymers.xlsx", {k: (t, T, *tga(v, T)) for k, v in polymers.items()}, head)

    cnt = {"Raw": [(1.5, 90, 18), (9, 430, 30), (74.5, 590, 35)],         # 15 % catalyst oxide
           "Acid-washed": [(3, 95, 20), (6, 420, 30), (86, 575, 32)],
           "Annealed": [(0.5, 90, 15), (1.5, 450, 30), (96, 640, 28)]}
    write_xlsx(dest / "cnt_batches.xlsx", {k: (t, T, *tga(v, T)) for k, v in cnt.items()}, head)

    # two lots of the same CNT as text files in two different styles
    write_csv(dest / "cnt_lot_A.csv", head, (t, T, *tga([(1, 90, 15), (89, 610, 30)], T)))
    write_csv(dest / "cnt_lot_B.txt", head, (t, T, *tga([(2, 90, 15), (91, 585, 34)], T)),
              sep=";", decimal=",")

    # calcium oxalate monohydrate in air: -H2O, -CO (burns: exothermic), -CO2, CaO left
    T2 = np.arange(30.0, 950.1, 1.0)
    W, D = tga([(12.3, 185, 18), (19.2, 505, 15), (30.1, 735, 22)], T2)
    HF = (0.05 + 0.0001 * T2 - 1.1 * gauss(T2, 185, 16) + 2.2 * gauss(T2, 507, 13)
          - 1.5 * gauss(T2, 737, 20) + rng.normal(0, 0.006, T2.size))
    write_csv(dest / "caox.csv", head + ["Heat Flow (W/g)"], ((T2 - 30) / 10, T2, W, D, HF))

    # isothermal: 20 °C/min to 400 °C, then 2 h at 400 °C in air
    tm = np.arange(0, 140.01, 0.25)
    Tp = np.minimum(30 + 20 * tm, 400)
    hold = np.clip(tm - 18.5, 0, None)
    Wi = 100 - 0.9 / (1 + np.exp(-(Tp - 110) / 12)) - 26 * (1 - np.exp(-hold / 48))
    write_csv(dest / "isothermal.txt", ["Time (min)", "Temperature (°C)", "Weight (%)"],
              (tm, Tp, Wi + rng.normal(0, 0.01, tm.size)), sep="\t")

    # XRD pattern (anatase-like positions)
    th = np.arange(10, 80.001, 0.02)
    I = 40 + 160 * np.exp(-th / 25)
    for pos, h in [(25.3, 1000), (37.8, 190), (48.0, 330), (53.9, 200), (55.1, 190), (62.7, 140),
                   (68.8, 60), (70.3, 65), (75.0, 90)]:
        I = I + h * (0.6 / (1 + ((th - pos) / 0.18) ** 2) + 0.4 * gauss(th, pos, 0.16))
    write_csv(dest / "xrd.csv", ["2Theta (deg)", "Intensity (counts)"], (th, rng.poisson(I).astype(float)))

    # frequency sweep of a viscoelastic melt (two Maxwell modes)
    w = np.logspace(-2, 2, 29)
    Gp = sum(G * (w * tau) ** 2 / (1 + (w * tau) ** 2) for G, tau in [(8e4, 1.0), (4e4, 0.05)])
    Gpp = sum(G * (w * tau) / (1 + (w * tau) ** 2) for G, tau in [(8e4, 1.0), (4e4, 0.05)])
    noise = lambda n: np.exp(rng.normal(0, 0.03, n))  # noqa: E731
    write_csv(dest / "rheology.csv",
              ["Angular frequency (rad/s)", "Storage modulus G' (Pa)", "Loss modulus G'' (Pa)"],
              (w, Gp * noise(w.size), Gpp * noise(w.size)))


# =================================================================== the specs
GALLERY = []


def add(section, title, shows, spec, engines=ENGINES):
    GALLERY.append({"id": f"{len(GALLERY) + 1:02d}", "section": section, "title": title, "shows": shows,
                    "spec": spec, "engines": engines})


S = "Start from almost nothing"
add(S, "Only the file and a sheet",
    "Everything else comes from the TGA preset: axis labels, colours, the DTG on the right axis, "
    "the residue at 800 °C and the main DTG peak.",
    {"file": "data/polymers.xlsx", "sheets": "PVC"})
add(S, "Every sheet, one plot each",
    "No sheet named: one PNG per sheet, the same settings for all.",
    {"file": "data/polymers.xlsx"})
add(S, "More peaks, residue somewhere else",
    "Two numbers change the preset labels: three DTG peaks, and the residue read at 900 °C with its own text.",
    {"file": "data/caox.csv", "annotate": {"peak": {"count": 3}, "residue": {"x": 900, "text": "CaO {y:.1f}%"}}})

S = "Annotations"
add(S, "Shade and name each step",
    "Three band annotations with their own colour and text, on top of the preset labels.",
    {"file": "data/caox.csv",
     "annotate": {"peak": {"count": 3}, "residue": {"x": 900},
                  "band_h2o": {"type": "band", "x_min": 120, "x_max": 250, "color": "#2a7fd4", "alpha": 0.12,
                               "text": "−H2O"},
                  "band_co": {"type": "band", "x_min": 430, "x_max": 580, "color": "#d98a00", "alpha": 0.12,
                              "text": "−CO"},
                  "band_co2": {"type": "band", "x_min": 640, "x_max": 830, "color": "#7b4fc4", "alpha": 0.12,
                               "text": "−CO2"}}})
add(S, "Mass at chosen temperatures, plus a theory line",
    "Preset labels off; three value_at_x labels with a template that prints both x and y, and an hline.",
    {"file": "data/caox.csv", "y2": False,
     "annotate": {"residue": False, "peak": False,
                  "w300": {"type": "value_at_x", "x": 300, "text": "{y:.1f}% at {x:.0f} °C"},
                  "w600": {"type": "value_at_x", "x": 600, "text": "{y:.1f}% at {x:.0f} °C"},
                  "w900": {"type": "value_at_x", "x": 900, "text": "{y:.1f}% at {x:.0f} °C"},
                  "theory": {"type": "hline", "on": "y1", "y": 38.4, "text": "CaO, theory 38.4 %",
                             "linestyle": "dotted"}}})
add(S, "Reference lines and a note",
    "A vertical line, a horizontal line on the weight axis and a free text note in a corner.",
    {"file": "data/polymers.xlsx", "sheets": "PVC",
     "annotate": {"onset": {"type": "vline", "x": 250, "text": "HCl release starts"},
                  "half": {"type": "hline", "on": "y1", "y": 50, "text": "half the mass"},
                  "note": {"type": "text", "text": "PVC · 10 °C/min · N2", "where": "upper right"}}})
add(S, "Small peaks inside a window",
    "count, min_rel and x_min pick up the moisture and amorphous-carbon peaks next to the main one.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Raw",
     "annotate": {"peak": {"count": 3, "min_rel": 0.03, "x_min": 50},
                  "residue": {"text": "catalyst oxide {y:.1f}%"}}})
add(S, "Label templates, interpolation, label style",
    "Residue interpolated at 750 °C with three decimals; peak label with its own text, size and colour.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Annealed",
     "annotate": {"residue": {"x": 750, "method": "interp", "text": "{y:.3f}% at {x:.0f} °C"},
                  "peak": {"text": "Tmax = {x:.1f} °C", "size": 12, "color": "black"}}})
add(S, "Heat flow on the right axis: endo and exo peaks",
    "y2 switched to another column; two peak annotations, one looking for minima (endo), one for maxima (exo).",
    {"file": "data/caox.csv",
     "y2": {"col": "Heat Flow", "label": "Heat flow (W/g, exo up)", "flip": "none", "color": "#b03a2e"},
     "annotate": {"peak": False,
                  "endo": {"type": "peak", "on": "y2", "kind": "min", "count": 2, "text": "endo {x:.0f} °C"},
                  "exo": {"type": "peak", "on": "y2", "kind": "max", "text": "exo {x:.0f} °C"}}})
add(S, "DTG pointing down",
    "The preset flips the DTG so peaks point up; flip none keeps the raw sign and the peak label looks for a minimum.",
    {"file": "data/polymers.xlsx", "sheets": "PET",
     "y2": {"flip": "none"}, "annotate": {"peak": {"kind": "min"}}})

S = "Lines, axes and text"
add(S, "Line colour, width and style (Korean colour names)",
    "초록 and 보라 are read as green and purple.",
    {"file": "data/polymers.xlsx", "sheets": "PE",
     "y1": {"color": "초록", "width": 3, "linestyle": "dashed"},
     "y2": {"color": "보라", "width": 1, "linestyle": "dotted"}})
add(S, "Axis ranges, tick steps, tick and label colours",
    "min / max / step on all three axes, black tick numbers on the left, larger y2 label, ticks outside.",
    {"file": "data/polymers.xlsx", "sheets": "PVC", "tick_direction": "out",
     "x": {"min": 100, "max": 700, "step": 100},
     "y1": {"min": 0, "max": 105, "step": 25, "label_color": "black", "tick_color": "black"},
     "y2": {"min": 0, "max": 1.4, "step": 0.35, "label_size": 13}})
add(S, "Zoom into the first step",
    "A narrow x range, a tight y1 range, the peak search limited to the window and a new value label.",
    {"file": "data/caox.csv",
     "x": {"min": 100, "max": 300, "step": 25}, "y1": {"min": 85, "max": 101},
     "annotate": {"residue": False, "peak": {"x_min": 100, "x_max": 300},
                  "after": {"type": "value_at_x", "x": 260, "text": "{y:.2f}% after dehydration"}}})
add(S, "Black and grey for print",
    "Line colours plus text_color; the labels follow text_color instead of the line colours.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Acid-washed", "text_color": "black",
     "y1": {"color": "black"}, "y2": {"color": "gray", "linestyle": "dashed"},
     "legend": {"where": "upper right"}})
add(S, "Korean everywhere",
    "Title, axis labels, legend names and label templates in Korean; the Korean font is picked automatically.",
    {"file": "data/polymers.xlsx", "sheets": "PET", "font_size": 12,
     "title": "PET 열분해 (질소, 10 °C/min)",
     "x": {"label": "온도 (°C)"}, "y1": {"label": "무게 (%)", "legend": "무게"},
     "y2": {"label": "미분 무게 (%/°C)", "legend": "미분 무게"},
     "annotate": {"residue": {"text": "잔류량 {y:.1f}%"}, "peak": {"text": "최대 분해 {x:.0f} °C"}}})
add(S, "Small figure for a journal column",
    "3.4 × 2.6 in at 600 dpi, 8 pt text, no title, no legend, ticks outside.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Annealed", "size": [3.4, 2.6], "dpi": 600, "font_size": 8,
     "title": "", "legend": "none", "tick_direction": "out"})
add(S, "Wide slide figure",
    "11 × 4 in, big text, a styled title, grid on, legend moved and enlarged.",
    {"file": "data/polymers.xlsx", "sheets": "PVC", "size": [11, 4], "font_size": 15, "grid": True,
     "title": {"text": "PVC loses HCl first, then its backbone", "size": 20, "color": "#1f4e9c"},
     "legend": {"where": "lower left", "size": 13}})
add(S, "All text grey, title from the file name",
    "text_color and font_size change every text; {file} in the title is replaced by the file name.",
    {"file": "data/caox.csv", "title": "{file}: CaC2O4·H2O in air", "text_color": "dimgray", "font_size": 12})

S = "Several sheets and files"
add(S, "All sheets in one figure",
    "combine: one colour per sheet; weight solid, DTG dashed; residue and peak labels per sheet.",
    {"file": "data/cnt_batches.xlsx", "combine": True})
add(S, "Chosen sheets, weight only",
    "Sheets by number, no right axis, residue read at 600 °C with a short label.",
    {"file": "data/polymers.xlsx", "sheets": [1, 3], "combine": True, "y2": False,
     "legend": "lower left", "annotate": {"residue": {"x": 600, "text": "{y:.1f}%"}}})
add(S, "Two files in two formats, one figure",
    "A comma CSV and a semicolon text file with decimal commas, overlaid; the reader works out both.",
    {"file": ["data/cnt_lot_A.csv", "data/cnt_lot_B.txt"], "combine": True, "title": "Lot A vs Lot B"})

S = "Not TGA"
add(S, "Isothermal hold: time on x, temperature on the right",
    "preset none: any columns on any axis. A vertical line marks the hold, a value label the end.",
    {"file": "data/isothermal.txt", "preset": "none", "title": "CNT in air, 2 h at 400 °C",
     "x": {"col": "Time", "step": 20}, "y1": {"col": "Weight"},
     "y2": {"col": "Temperature", "color": "#c0392b", "linestyle": "dashed"},
     "annotate": {"hold": {"type": "vline", "x": 18.5, "text": "hold at 400 °C"},
                  "end": {"type": "value_at_x", "x": 140, "text": "{y:.1f}% after 2 h"}}})
add(S, "XRD pattern with labelled peaks",
    "One axis, peaks on y1 with a degree template, no legend.",
    {"file": "data/xrd.csv", "preset": "none", "y2": False, "legend": "none",
     "title": "Anatase TiO2 (made-up)",
     "x": {"col": "2Theta", "label": "2θ (°)", "step": 10},
     "y1": {"col": "Intensity", "color": "black", "width": 1},
     "annotate": {"peaks": {"type": "peak", "on": "y1", "count": 6, "min_rel": 0.1, "text": "{x:.1f}°"}}})
add(S, "Log–log with markers",
    "Both axes logarithmic with the same range, markers on y1, scatter on y2, a line at the crossover.",
    {"file": "data/rheology.csv", "preset": "none", "title": "Frequency sweep at 190 °C",
     "x": {"col": "frequency", "log": True, "label": "ω (rad/s)"},
     "y1": {"col": "Storage", "log": True, "min": 100, "max": 200000, "style": "line+marker",
            "label": "G′ (Pa)", "legend": "G′ storage"},
     "y2": {"col": "Loss", "log": True, "min": 100, "max": 200000, "style": "scatter",
            "label": "G″ (Pa)", "legend": "G″ loss"},
     "legend": "lower right",
     "annotate": {"cross": {"type": "vline", "x": 1.4, "text": "G′ = G″"}}})

S = "When no key fits"
add(S, "\"code\": a few matplotlib lines",
    "Fill under the weight curve, an arrow with text, no top frame line. Python, so matplotlib only.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Raw",
     "code": "ax1.fill_between(x, y1, color='#1f4e9c', alpha=0.08)\n"
             "ax1.annotate('catalyst residue', xy=(850, 16), xytext=(640, 45), color='gray',\n"
             "             arrowprops=dict(arrowstyle='->', color='gray'))\n"
             "ax1.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)"},
    engines=("matplotlib",))
add(S, "\"echarts\": the same in an ECharts patch",
    "The same three changes as a JSON patch merged over the ECharts option, checked against an allowlist.",
    {"file": "data/cnt_batches.xlsx", "sheets": "Raw",
     "echarts": {"series": [{"areaStyle": {"opacity": 0.08},
                             "markLine": {"symbol": ["none", "arrow"], "lineStyle": {"color": "gray", "type": "solid"},
                                          "label": {"formatter": "catalyst residue", "color": "gray"},
                                          "data": [[{"coord": [640, 45]}, {"coord": [850, 16]}]]}}],
                 "grid": {"show": False}}},
    engines=("echarts",))


# =================================================================== draw
def absolute(spec):
    s = copy.deepcopy(spec)
    files = s["file"] if isinstance(s["file"], list) else [s["file"]]
    files = [str(HERE / f) for f in files]
    s["file"] = files if isinstance(spec["file"], list) else files[0]
    return s


def draw(item, engine):
    outdir = OUT / engine / item["id"]
    shutil.rmtree(outdir, ignore_errors=True)
    s = absolute(item["spec"])
    s["output"] = {**s.get("output", {}), "dir": str(outdir)}
    try:
        res = plotkit.plot(s, engine=engine)
    except plotkit.PlotkitError as e:
        return {"error": e.message, "hint": e.hint}
    pngs = [p for r in res["plots"] for p in r["saved"] if p.endswith(".png")]
    return {"pngs": pngs, "warnings": res.get("warnings", [])}


def other(engine):
    return ENGINES[1 - ENGINES.index(engine)]


# =================================================================== page
CSS = """
:root{--ink:#1d2330;--mute:#5b6372;--line:#e3e1dc;--paper:#faf9f6;--card:#fff;--accent:#1f4e9c}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.5 "Inter","Segoe UI",system-ui,sans-serif}
header{padding:40px 48px 8px;max-width:1500px;margin:auto}
h1{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}
header p{color:var(--mute);max-width:820px;margin:6px 0}
nav{max-width:1500px;margin:8px auto 0;padding:0 48px;display:flex;flex-wrap:wrap;gap:8px}
nav a{font-size:13px;color:var(--accent);text-decoration:none;border:1px solid var(--line);
background:var(--card);padding:4px 10px;border-radius:99px}
main{max-width:1500px;margin:auto;padding:8px 48px 64px}
h2{font-size:19px;margin:36px 0 12px;padding-top:12px;border-top:2px solid var(--ink)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:14px 0;
display:grid;grid-template-columns:minmax(300px,380px) 1fr;overflow:hidden}
.spec{padding:16px 18px;border-right:1px solid var(--line)}
.spec h3{font-size:15px;margin:0 0 4px}.num{color:var(--mute);font-variant-numeric:tabular-nums;margin-right:6px}
.shows{color:var(--mute);font-size:13.5px;margin:0 0 10px}
pre{margin:0;background:#f4f3ef;border-radius:6px;padding:10px 12px;font:12px/1.45 ui-monospace,
"JetBrains Mono",Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
.plots{display:grid;grid-template-columns:1fr 1fr;gap:0}
.eng{padding:12px 14px}.eng+.eng{border-left:1px solid var(--line)}
.eng h4{margin:0 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.eng img{width:100%;display:block;border:1px solid #eee;border-radius:4px;margin-bottom:6px;background:#fff}
.err{font-size:13px;color:#8a2a1d;background:#fbeeea;border-radius:6px;padding:8px 10px}
.err code{font-size:12px}.warn{font-size:12px;color:#8a6d1d}
@media (max-width:1000px){.card{grid-template-columns:1fr}.spec{border-right:0;border-bottom:1px solid var(--line)}}
"""


def page(items, results):
    sections = list(dict.fromkeys(i["section"] for i in items))
    parts = ["<!DOCTYPE html><html lang='en'><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>plotkit spec gallery</title>", f"<style>{CSS}</style>",
             "<header><h1>What a plotkit spec can do</h1>",
             f"<p>{len(items)} specs on made-up data (polymers, calcium oxalate, CNT batches, an isothermal hold, "
             "XRD, rheology). Each card shows the spec exactly as plotkit received it, drawn by matplotlib (left) and "
             "ECharts (right). The gallery script only adds <code>output.dir</code> and absolute file paths.</p>",
             "<p>Rebuild: <code>python experiments/gallery/make_gallery.py</code>. Specs: <code>gallery/specs/</code>.</p></header>",
             "<nav>" + "".join(f"<a href='#s{k}'>{html.escape(s)}</a>" for k, s in enumerate(sections)) + "</nav><main>"]
    for k, sec in enumerate(sections):
        parts.append(f"<h2 id='s{k}'>{html.escape(sec)}</h2>")
        for it in (i for i in items if i["section"] == sec):
            cells = []
            for eng in ENGINES:
                res = results[(it["id"], eng)]
                body = ""
                if "error" in res:
                    why = ("this key is for the other engine; plotkit answers:" if eng not in it["engines"]
                           else "plotkit rejected the spec:")
                    body = (f"<div class='err'>{why}<br><code>{html.escape(res['error'])}</code>"
                            + (f"<br>hint: <code>{html.escape(res['hint'])}</code>" if res.get("hint") else "")
                            + "</div>")
                else:
                    body = "".join(f"<img loading='lazy' src='{html.escape(Path(p).relative_to(HERE).as_posix())}'>"
                                   for p in res["pngs"])
                    body += "".join(f"<div class='warn'>warning: {html.escape(w)}</div>" for w in res["warnings"])
                cells.append(f"<div class='eng'><h4>{'matplotlib' if eng == 'matplotlib' else 'ECharts'}</h4>{body}</div>")
            spec_txt = json.dumps(it["spec"], ensure_ascii=False, indent=2)
            parts.append(f"<section class='card' id='g{it['id']}'><div class='spec'>"
                         f"<h3><span class='num'>{it['id']}</span>{html.escape(it['title'])}</h3>"
                         f"<p class='shows'>{html.escape(it['shows'])}</p><pre>{html.escape(spec_txt)}</pre></div>"
                         f"<div class='plots'>{''.join(cells)}</div></section>")
    parts.append("</main></html>")
    (HERE / "index.html").write_text("\n".join(parts), encoding="utf-8")


def contact_pages(items, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for n in range(0, len(items), 6):
        chunk = items[n:n + 6]
        fig, axs = plt.subplots(len(chunk), 2, figsize=(11, 3.9 * len(chunk)), squeeze=False)
        for i, it in enumerate(chunk):
            for j, eng in enumerate(ENGINES):
                ax = axs[i][j]
                ax.axis("off")
                res = results[(it["id"], eng)]
                if res.get("pngs"):
                    ax.imshow(plt.imread(res["pngs"][0]))
                elif "error" in res:
                    ax.text(0.5, 0.5, "error: " + res["error"][:90], ha="center", va="center", wrap=True, fontsize=8)
                ax.set_title(f"{it['id']} {it['title'][:55]} - {eng}", fontsize=8)
        fig.tight_layout()
        p = HERE / f"pages_{n // 6 + 1}.png"
        fig.savefig(p, dpi=100)
        plt.close(fig)
        print("wrote", p.relative_to(ROOT))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated ids to redraw, e.g. 03,24")
    ap.add_argument("--pages", action="store_true", help="also write gallery/pages_N.png")
    a = ap.parse_args()
    make_data()
    SPECS.mkdir(exist_ok=True)
    only = {x.zfill(2) for x in a.only.split(",")} if a.only else None
    cache = HERE / "out" / "results.json"
    results = {}
    if only and cache.exists():
        results = {tuple(k.split("|")): v for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
    for it in GALLERY:
        slug = "".join(c if c.isalnum() else "_" for c in it["title"].lower()).strip("_")[:40]
        (SPECS / f"{it['id']}_{slug}.json").write_text(json.dumps(it["spec"], ensure_ascii=False, indent=2) + "\n",
                                                       encoding="utf-8")
        if only and it["id"] not in only and all((it["id"], e) in results for e in ENGINES):
            continue
        for eng in ENGINES:
            res = draw(it, eng)
            results[(it["id"], eng)] = res
            status = ("error: " + res["error"]) if "error" in res else f"{len(res['pngs'])} png"
            flag = "" if ("error" in res) == (eng not in it["engines"]) else "   <-- unexpected"
            print(f"{it['id']} {eng:10s} {status}{flag}")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"|".join(k): v for k, v in results.items()}, ensure_ascii=False), encoding="utf-8")
    page(GALLERY, results)
    print("wrote", (HERE / "index.html").relative_to(ROOT))
    if a.pages:
        contact_pages(GALLERY, results)


if __name__ == "__main__":
    main()
