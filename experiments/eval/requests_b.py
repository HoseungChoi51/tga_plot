"""Set B: 24 requests the protocol was not written for, on the gallery's made-up data (eval/inputs_b/).

    in scope, not rehearsed (B01-B08) | messy wording (B09-B14) | out of scope: no spec key (B15-B24)

    python experiments/eval/requests_b.py      -> eval/requests_b.md (same layout as tests/AGENT_TEST_PROMPTS.md)
"""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
D = "eval/inputs_b/"

# (id, group, files, Korean request)
REQUESTS = [
    ("B01_bands", "in", [D + "caox.csv"],
     "질량이 줄어드는 세 구간(120~250, 430~580, 640~830 °C)을 각각 다른 색으로 연하게 칠하고, 구간 위에 H2O, CO, CO2라고 써줘"),
    ("B02_heat_flow_peaks", "in", [D + "caox.csv"],
     "오른쪽 축에 DTG 대신 Heat Flow를 그리고, 흡열 피크 두 개와 발열 피크 하나의 온도를 표시해줘"),
    ("B03_log_axes", "in", [D + "rheology.csv"],
     "주파수에 따른 G'(왼쪽 축)와 G''(오른쪽 축)를 그려줘. x축과 두 y축 모두 로그 스케일로"),
    ("B04_xrd_peaks", "in", [D + "xrd.csv"],
     "XRD 패턴 그려주고 강한 피크 5개의 2θ 값을 표시해줘. 오른쪽 축은 필요 없어"),
    ("B05_two_files", "out", [D + "cnt_lot_A.csv", D + "cnt_lot_B.txt"],
     "두 파일을 한 그림에 겹쳐 그리고 범례에는 Lot A, Lot B라고 써줘"),
    ("B06_time_axis", "in", [D + "isothermal.txt"],
     "시간(분)을 x축으로, 무게는 왼쪽 축, 온도는 오른쪽 축에 그려줘. 140분일 때 무게를 표시해줘"),
    ("B07_sheet_number", "in", [D + "polymers.xlsx"],
     "두 번째 시트만 그리고, 300 °C와 600 °C에서의 무게를 표시해줘"),
    ("B08_hline_note", "in", [D + "cnt_batches.xlsx"],
     "Raw 시트에 무게 50% 위치에 가로 보조선 넣고, 오른쪽 위에 '공기, 10 °C/min'이라고 메모해줘"),
    ("B09_typos", "messy", [D + "polymers.xlsx"],
     "PE시트 그래프 x축 범위 100~700 으로하고 틱간격 100, y1 선 굵게(3) 빨간색으로 해주세용"),
    ("B10_paper_bw", "messy", [D + "cnt_batches.xlsx"],
     "Annealed 시트 논문에 넣을 거라 흑백으로 해줘. 글자 크기 8, 그림 3.5×2.6 인치, 600 dpi"),
    ("B11_many_changes", "messy", [D + "polymers.xlsx"],
     "PET 시트, 제목은 'PET 열분해', 범례는 왼쪽 아래, 격자 켜고, 잔류량은 소수 둘째 자리까지"),
    ("B12_english", "messy", [D + "caox.csv"],
     "Please plot the weight curve only (no DTG), x range 100 to 900, and label the residue at 900 °C"),
    ("B13_vague_term", "messy", [D + "polymers.xlsx"],
     "PVC 시트에서 무게가 확 꺾이는 데 두 군데 온도 표시해줘"),
    ("B14_slide", "messy", [D + "polymers.xlsx"],
     "PVC 시트 발표 슬라이드용으로 크게. 가로 10인치, 글자 16"),
    ("B15_legend_outside", "out", [D + "polymers.xlsx"],
     "세 시트 겹쳐 그리고 범례는 그래프 바깥 오른쪽에 둬"),
    ("B16_two_panels", "out", [D + "caox.csv"],
     "무게는 위 그래프, DTG는 아래 그래프로 따로 나눠서 그려줘 (x축은 같이)"),
    ("B17_offset", "out", [D + "polymers.xlsx"],
     "세 시트 무게 곡선을 겹치지 않게 20%씩 위아래로 띄워서(offset) 한 그림에 그려줘"),
    ("B18_onset", "out", [D + "cnt_batches.xlsx"],
     "Annealed 시트에서 외삽 개시 온도(onset)를 구해서 그래프에 표시해줘"),
    ("B19_mass_loss", "out", [D + "polymers.xlsx"],
     "PVC 시트에서 200 °C부터 400 °C 사이 질량 감소량(%)을 계산해서 그래프에 표시해줘"),
    ("B20_minor_ticks", "out", [D + "cnt_batches.xlsx"],
     "Acid-washed 시트, x축에 보조 눈금(minor tick)도 넣어줘"),
    ("B21_reversed_x", "out", [D + "cnt_batches.xlsx"],
     "Raw 시트를 x축 방향 뒤집어서(높은 온도가 왼쪽) 그려줘"),
    ("B22_dry_basis", "out", [D + "cnt_batches.xlsx"],
     "Raw 시트를 150 °C 무게를 100%로 다시 계산해서(건조 기준) 그려줘"),
    ("B23_sample_colors", "out", [D + "cnt_batches.xlsx"],
     "세 시료 겹쳐서 그리고 Raw는 검정, Acid-washed는 파랑, Annealed는 빨강으로 해줘"),
    ("B24_kelvin", "out", [D + "polymers.xlsx"],
     "PE 시트를 온도 단위 켈빈(K)으로 바꿔서 그려줘"),
]


def write_md():
    out = ["# Set B requests (evaluation)", "",
           "Made with `python experiments/eval/requests_b.py`. Data: `eval/inputs_b/` (gallery generator). "
           "Groups: in = a key exists but no example covers it, messy = unusual wording, out = no spec key exists.", ""]
    for rid, group, files, text in REQUESTS:
        out += [f"## {rid}", "", f"group: {group}", "", "```text", "파일: " + ", ".join(files), text, "```", ""]
    (HERE / "requests_b.md").write_text("\n".join(out), encoding="utf-8")


def expectations_b(rng, at, job):
    """Checks per request; rng/at/job read truths from the data through plotkit's reader."""
    CA, PO, CN, RH, XR, IS = (D + n for n in ("caox.csv", "polymers.xlsx", "cnt_batches.xlsx", "rheology.csv",
                                              "xrd.csv", "isothermal.txt"))
    W = lambda f, s=None: rng(f, "y1", sheet=s)                       # noqa: E731
    E = {}
    E["B01"] = [{"series": {"axis": "y1", "y_range": W(CA)}, "cat": "data"},
                {"spans": [[120, 250], [430, 580], [640, 830]], "tol": 6},
                {"text_contains": "H2O"}, {"text_contains": "CO2"}]
    hf = job(CA, y2="E")
    x, h = hf["x"], hf["y2"]
    endo1 = float(x[(x < 300)][np.argmin(h[x < 300])])
    endo2 = float(x[(x > 650)][np.argmin(h[x > 650])])
    exo = float(x[np.argmax(h)])
    E["B02"] = [{"series": {"axis": "y2", "y_range": rng(CA, "y2", y2="E")}, "cat": "data"},
                {"text_values": {"values": [endo1, endo2, exo], "tol": 6}},
                {"axis": {"which": "y2", "label_contains": "heat"}}]
    E["B03"] = [{"series": {"axis": "y1", "y_range": rng(RH, "y1", preset="none", x="A", y1="B")}, "cat": "data"},
                {"series": {"axis": "y2", "y_range": rng(RH, "y2", preset="none", x="A", y1="B", y2="C")}, "cat": "data"},
                {"axis": {"which": "x", "scale": "log"}}, {"axis": {"which": "y1", "scale": "log"}},
                {"axis": {"which": "y2", "scale": "log"}}]
    E["B04"] = [{"series": {"axis": "y1", "y_range": rng(XR, "y1", preset="none", x="A", y1="B")}, "cat": "data"},
                {"no_y2": True}, {"text_values": {"values": [25.3, 48.0, 53.9, 37.8, 55.1], "tol": 0.3}}]
    E["B05"] = [{"series_set": {"axis": "y1", "ranges": [W(D + "cnt_lot_A.csv"), W(D + "cnt_lot_B.txt")],
                                "same_figure": True}, "cat": "data"},
                {"text_contains": "Lot A"}, {"text_contains": "Lot B"}]
    E["B06"] = [{"series": {"axis": "y1", "x_range": [0, 140],
                            "y_range": rng(IS, "y1", preset="none", x="A", y1="C")}, "cat": "data"},
                {"series": {"axis": "y2", "y_range": rng(IS, "y2", preset="none", x="A", y1="C", y2="B")}, "cat": "data"},
                {"text_value": {"value": at(IS, 140, preset="none", x="A", y1="C"), "tol": 0.1}}]
    E["B07"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PVC")]}, "cat": "data"},
                {"text_value": {"value": at(PO, 300, sheet="PVC"), "tol": 0.15}},
                {"text_value": {"value": at(PO, 600, sheet="PVC"), "tol": 0.15}}]
    E["B08"] = [{"only": {"axis": "y1", "ranges": [W(CN, "Raw")]}, "cat": "data"},
                {"hline": {"y": 50, "axis": "y1"}}, {"text_contains": "공기, 10 °C/min"}]
    E["B09"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PE")]}, "cat": "data"},
                {"axis": {"which": "x", "min": 100, "max": 700, "step": 100}},
                {"lines": {"axis": "y1", "color": "red", "width": 3}}]
    E["B10"] = [{"only": {"axis": "y1", "ranges": [W(CN, "Annealed")]}, "cat": "data"},
                {"lines": {"axis": "y1", "color": "black"}}, {"lines": {"axis": "y2", "color": ["black", "gray"]}},
                {"png_px": [2100, 1560]}, {"axis": {"which": "x", "label_size": 8}}]
    E["B11"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PET")]}, "cat": "data"},
                {"title": {"text": "PET 열분해"}}, {"legend": {"where": "lower left"}}, {"grid": True},
                {"text_value": {"value": at(PO, 800, sheet="PET"), "tol": 0.03, "regex": r"\d+\.\d{2}(?!\d)"}}]
    E["B12"] = [{"series": {"axis": "y1", "y_range": W(CA)}, "cat": "data"}, {"no_y2": True},
                {"axis": {"which": "x", "min": 100, "max": 900}},
                {"text_value": {"value": at(CA, 900), "tol": 0.1}}]
    E["B13"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PVC")]}, "cat": "data"},
                {"text_values": {"values": [300, 455], "tol": 8}}]
    E["B14"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PVC")]}, "cat": "data"},
                {"size_in": {"w": 10}}, {"font_size": 16}]
    allp = [W(PO, s) for s in ("PE", "PVC", "PET")]
    E["B15"] = [{"series_set": {"axis": "y1", "ranges": allp, "same_figure": True}, "cat": "data"},
                {"legend": {"shown": True, "inside": False}}]
    E["B16"] = [{"series": {"axis": "any", "y_range": W(CA)}, "cat": "data"},
                {"series": {"axis": "any", "y_range": rng(CA, "y2"), "abs": True}, "cat": "data"},
                {"panels": {"min": 2}}]
    E["B17"] = [{"offset": {"n": 3, "min_gap": 10}}]
    ann = job(CN, sheet="Annealed")
    xa, wa = ann["x"], ann["y1"]
    dw = np.gradient(wa, xa)
    k = int(np.argmin(np.convolve(dw, np.ones(9) / 9, mode="same")))
    base = float(np.median(wa[(xa > 520) & (xa < 560)]))
    onset = float(xa[k] + (base - wa[k]) / np.convolve(dw, np.ones(9) / 9, mode="same")[k])
    E["B18"] = [{"only": {"axis": "y1", "ranges": [W(CN, "Annealed")]}, "cat": "data"},
                {"text_value": {"value": round(onset, 1), "tol": 8}}]
    E["B19"] = [{"only": {"axis": "y1", "ranges": [W(PO, "PVC")]}, "cat": "data"},
                {"text_value": {"value": round(at(PO, 200, sheet="PVC") - at(PO, 400, sheet="PVC"), 2), "tol": 0.6}}]
    E["B20"] = [{"only": {"axis": "y1", "ranges": [W(CN, "Acid-washed")]}, "cat": "data"},
                {"axis": {"which": "x", "minor": True}}]
    E["B21"] = [{"only": {"axis": "y1", "ranges": [W(CN, "Raw")]}, "cat": "data"},
                {"axis": {"which": "x", "inverted": True}}]
    raw = job(CN, sheet="Raw")
    w150 = float(raw["y1"][int(np.argmin(np.abs(raw["x"] - 150)))])
    E["B22"] = [{"series": {"axis": "y1", "y_range": [float(raw["y1"].min() / w150 * 100),
                                                      float(raw["y1"].max() / w150 * 100)], "tol": 0.01}}]
    cn = {s: W(CN, s) for s in ("Raw", "Acid-washed", "Annealed")}
    E["B23"] = [{"series_set": {"axis": "y1", "ranges": list(cn.values()), "same_figure": True}, "cat": "data"},
                {"line_color": {"axis": "y1", "y_range": cn["Raw"], "color": "black"}},
                {"line_color": {"axis": "y1", "y_range": cn["Acid-washed"], "color": "blue"}},
                {"line_color": {"axis": "y1", "y_range": cn["Annealed"], "color": "red"}}]
    xr = rng(PO, "x", sheet="PE")
    E["B24"] = [{"series": {"axis": "y1", "x_range": [xr[0] + 273.15, xr[1] + 273.15], "y_range": W(PO, "PE"),
                            "tol": 0.01}},
                {"axis": {"which": "x", "label_contains": "K"}}]
    return E


if __name__ == "__main__":
    write_md()
    print(f"{len(REQUESTS)} requests -> eval/requests_b.md")
