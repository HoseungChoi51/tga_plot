"""Expected figure facts for every evaluation request, with truths computed from the data files.

    python experiments/eval/expectations.py        -> eval/expected_facts.json
Set A = tests/AGENT_TEST_PROMPTS.md (ids 01-24), Set B = eval/requests_b.md (ids B01-B24).
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # experiments/
REPO = ROOT.parent                     # the library (plotkit, tests/inputs, prompts, echartkit, .venv)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ROOT))
import plotkit  # noqa: E402


@lru_cache(maxsize=None)
def job(file, sheet=None, x=None, y1=None, y2=None, preset="tga"):
    spec = {"file": str(REPO / file), "preset": preset}
    if sheet is not None:
        spec["sheets"] = sheet
    for k, v in (("x", x), ("y1", y1), ("y2", y2)):
        if v:
            spec[k] = {"col": v}
    if preset == "tga" and y2 is None:
        spec["y2"] = {"flip": "none"}            # truths keep the file's own sign; checks accept either
    jobs, _ = plotkit.build_jobs(plotkit.normalize_spec(spec))
    return jobs[0]["data"]


def rng(file, role, **kw):
    v = job(file, **kw)[role]
    return [round(float(np.min(v)), 6), round(float(np.max(v)), 6)]


def at(file, xv, role="y1", **kw):
    d = job(file, **kw)
    return round(float(d[role][int(np.argmin(np.abs(d["x"] - xv)))]), 6)


TGA = "tests/inputs/TGA.xlsx"
SHEETS = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"]


def dpeak(sheet, lo, hi, file=TGA):
    """Largest |DTG| between lo and hi °C (the peak's DTG value)."""
    d = job(file, sheet=sheet)
    m = (d["x"] >= lo) & (d["x"] <= hi)
    return round(float(np.max(np.abs(d["y2"][m]))), 4)


def W(sheet, file=TGA):
    return rng(file, "y1", sheet=sheet)


def D(sheet, file=TGA):
    return rng(file, "y2", sheet=sheet)


def set_a():
    allw = [W(s) for s in SHEETS]
    any_w = {"series": {"axis": "y1", "y_ranges": allw}, "cat": "data"}
    res_n = at(TGA, 800, sheet=SHEETS[0])
    E = {}
    E["01"] = [{"series_set": {"axis": "y1", "ranges": allw}, "cat": "data"},
               {"text_value": {"value": res_n, "tol": 0.1}, "cat": "conv"},
               {"text_value": {"value": at(TGA, 800, sheet=SHEETS[1]), "tol": 0.1}, "cat": "conv"},
               {"text_values": {"values": [600, 560, 540], "tol": 6}, "cat": "conv"}]
    E["02"] = [{"only": {"axis": "y1", "ranges": [W(SHEETS[0])]}, "cat": "data"},
               {"series": {"axis": "y2", "y_range": D(SHEETS[0]), "abs": True}, "cat": "data"},
               {"axis": {"which": "x", "min": 0, "step": 200}},
               {"axis": {"which": "y1", "step": 20}}, {"axis": {"which": "y2", "step": 0.2}},
               {"text_value": {"value": res_n, "tol": 0.1, "regex": r"^Residue \d+(\.\d+)?\s?%$"}},
               {"any_of": [{"text_values": {"values": [600], "tol": 6}},              # "Deriv.Weight max값": the peak's
                           {"text_value": {"value": dpeak(SHEETS[0], 150, 900), "tol": 0.03}}]},   # T or its DTG value
               {"formats": ["png"]}]
    E["03"] = [{"only": {"axis": "y1", "ranges": [W(SHEETS[1])]}, "cat": "data"},
               {"axis": {"which": "x", "min": 100, "max": 800}},
               {"any_of": [{"text_values": {"values": [560, 400], "tol": 8}},
                           {"text_values": {"values": [dpeak(SHEETS[1], 500, 650), dpeak(SHEETS[1], 330, 450)], "tol": 0.02}}]}]
    E["04"] = [{"only": {"axis": "y1", "ranges": [W(SHEETS[0])]}, "cat": "data"},
               {"title": {"text": "CNT 산화 거동", "size": 18, "color": "navy"}}]
    E["05"] = [any_w, {"lines": {"axis": "y1", "color": "black", "width": 2.5}},
               {"lines": {"axis": "y2", "style": "dotted"}}]
    E["06"] = [any_w, {"legend": {"shown": False}}, {"grid": True}]
    E["07"] = [any_w, {"legend": {"shown": True, "where": "upper right", "size": 9}}]
    E["08"] = [any_w, {"axis": {"which": "x", "label": "온도 (°C)"}}, {"axis": {"which": "y1", "label": "무게 (%)"}},
               {"axis": {"which": "y2", "label": "미분 무게 (%/°C)"}}]
    E["09"] = [any_w, {"axis": {"which": "x", "tick_direction": "out", "tick_size": 9}},
               {"axis": {"which": "y1", "tick_direction": "out", "tick_size": 9}},
               {"axis": {"which": "y2", "tick_size": 9}}]
    E["10"] = [any_w, {"text_value": {"value": at(TGA, 700, sheet=SHEETS[0]), "tol": 0.006,
                                      "regex": r"\d+\.\d{2}(?!\d)"}}]
    E["11"] = [any_w, {"no_text_value": {"value": 600, "tol": 6}}, {"no_text_value": {"value": 560, "tol": 6}},
               {"no_text_value": {"value": 540, "tol": 6}},
               {"text_value": {"value": res_n, "tol": 0.1}, "cat": "conv"}]
    E["12"] = [any_w, {"vline": {"x": 450}}, {"text_contains": "산화 시작"}]
    EX = "tests/inputs/extra_columns.xlsx"
    E["13"] = [{"series": {"axis": "y1", "y_range": rng(EX, "y1", y1="D")}, "cat": "data"},
               {"axis": {"which": "y1", "label": "Weight (mg)"}}]
    KC = "tests/inputs/korean_excel.csv"
    E["14"] = [{"series": {"axis": "y1", "y_range": rng(KC, "y1")}, "cat": "data"}, {"formats": ["pdf", "png"]}]
    E["15"] = [{"series_set": {"axis": "y1", "ranges": allw, "same_figure": True}}]
    E["16"] = [{"only": {"axis": "y1", "ranges": [W(SHEETS[0])]}, "cat": "data"}, {"no_y2": True}]
    E["17"] = [any_w, {"png_px": [4800, 3000]}]
    E["18"] = [any_w, {"axis": {"which": "x", "step": 100}}, {"axis": {"which": "y2", "min": -0.05, "max": 1.2}},
               {"visible": {"axis": "y2", "frac": 0.8}, "cat": "data"}]
    E["19"] = [any_w, {"text_color": "gray"}, {"font_size": 13}]
    E["20"] = [any_w, {"span": {"x_min": 300, "x_max": 450}}]
    BR = "tests/inputs/blank_rows_on_top.xlsx"
    E["21"] = [{"series": {"axis": "y1", "x_range": rng(BR, "x"), "y_range": rng(BR, "y1")}, "cat": "data"},
               {"series": {"axis": "y2", "y_range": rng(BR, "y2"), "abs": True}, "cat": "data"}]
    E["22"] = [any_w, {"lines": {"axis": "y2", "color": "green"}}, {"axis": {"which": "y2", "label_color": "green"}}]
    IE = "tests/inputs/instrument_export.txt"
    E["23"] = [{"series": {"axis": "y1", "y_range": rng(IE, "y1")}, "cat": "data"},
               {"text_value": {"value": at(IE, 800), "tol": 0.1, "regex": r"^Residue: \d+(\.\d+)?\s?%$"}}]
    E["24"] = [{"series": {"axis": "y2", "y_range": rng(EX, "y2", y2="F")}, "cat": "data"},
               {"axis": {"which": "y2", "label": "Heat flow (W/g)"}}, {"no_text_value": {"value": 600, "tol": 6}}]
    return E


def build():
    E = set_a()
    try:
        from requests_b import expectations_b
        E.update(expectations_b(rng=rng, at=at, job=job))
    except ImportError:
        pass
    (HERE / "expected_facts.json").write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")
    return E


if __name__ == "__main__":
    E = build()
    print(f"{len(E)} requests -> eval/expected_facts.json")
