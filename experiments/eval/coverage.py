"""Coverage: what plot changes a TGA user might plausibly ask for, and how (or whether) the protocol does each,
per engine. Every claimed route is drawn once; "blocked" specs must be refused by plotkit.

    python experiments/eval/coverage.py      -> eval/results/coverage.csv + coverage_summary.json

Routes: key = a spec key (both engines) | code = matplotlib "code" | echarts = ECharts "echarts" patch |
        partial = only part of the wish | none = not possible.
Sources: guide = the 15 parts of guide/guide_ko.png and its footer; tga = TGA practice;
         paper = journal/slide figure habits; lib = commonly used matplotlib/ECharts options.
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
sys.path.insert(0, str(HERE))
import paths  # noqa: E402
import facts  # noqa: E402
from plotkit import core as plotkit  # noqa: E402

T = "tests/inputs/TGA.xlsx"
EX = "tests/inputs/extra_columns.xlsx"
B = "eval/inputs_b/"
N = {"file": T, "sheets": 1}          # one sheet, for short demos

# (id, group, source, wish, example request, {route: spec}, note)
ITEMS = [
    # ---- data selection
    ("D1", "data", "guide", "pick a sheet", "1006R1-V acid 시트만", {"key": {"file": T, "sheets": "1006R1-V acid"}}, ""),
    ("D2", "data", "guide", "pick a sheet by number", "두 번째 시트", {"key": {"file": T, "sheets": 2}}, ""),
    ("D3", "data", "guide", "overlay all sheets", "시트 전부 겹쳐서", {"key": {"file": T, "combine": True}}, ""),
    ("D4", "data", "tga", "overlay several files", "두 파일 겹쳐서",
     {"key": {"file": [B + "cnt_lot_A.csv", B + "cnt_lot_B.txt"], "combine": True}}, ""),
    ("D5", "data", "guide", "choose columns", "C열을 y1축", {"key": {"file": EX, "y1": {"col": "D"}}}, ""),
    ("D6", "data", "lib", "any x–y data (not TGA)", "XRD 그려줘",
     {"key": {"file": B + "xrd.csv", "preset": "none", "x": {"col": "A"}, "y1": {"col": "B"}, "y2": False}}, ""),
    ("D7", "data", "tga", "rename combined curves in the legend", "범례에 Lot A, Lot B",
     {"code": {"file": [B + "cnt_lot_A.csv", B + "cnt_lot_B.txt"], "combine": True,
               "code": "for l, n in zip(ax1.get_lines()[:2], ['Lot A', 'Lot B']): l.set_label(n)\nax1.legend()"},
      "blocked_ec": {"file": [B + "cnt_lot_A.csv", B + "cnt_lot_B.txt"], "combine": True,
                     "echarts": {"legend": {"data": ["Lot A", "Lot B"]}}}},
     "ECharts: series names may change but legend.data may not, so renamed curves drop out of the legend"),
    ("D8", "data", "lib", "header row / first data row", "5행부터 데이터", {"key": {"file": T, "sheets": 1, "read": {"header_row": 1}}}, ""),
    # ---- axes
    ("A1", "axes", "guide", "axis range", "x축 0~900", {"key": dict(N, x={"min": 0, "max": 900})}, ""),
    ("A2", "axes", "guide", "tick spacing", "틱 간격 200", {"key": dict(N, x={"step": 200})}, ""),
    ("A3", "axes", "lib", "log axis", "로그 스케일",
     {"key": {"file": B + "rheology.csv", "preset": "none", "x": {"col": "A", "log": True}, "y1": {"col": "B", "log": True}}}, ""),
    ("A4", "axes", "paper", "reversed axis", "x축 뒤집기",
     {"code": dict(N, code="ax1.invert_xaxis()"), "echarts": dict(N, echarts={"xAxis": {"inverse": True}})}, ""),
    ("A5", "axes", "paper", "minor ticks", "보조 눈금",
     {"code": dict(N, code="ax1.minorticks_on()"), "echarts": dict(N, echarts={"xAxis": {"minorTick": {"show": True}}})}, ""),
    ("A6", "axes", "guide", "tick direction", "틱 바깥쪽", {"key": dict(N, tick_direction="out")}, ""),
    ("A7", "axes", "guide", "tick number size/colour", "틱 라벨 9", {"key": dict(N, x={"tick_size": 9, "tick_color": "gray"})}, ""),
    ("A8", "axes", "guide", "axis label text/size/colour", "x축 라벨 '온도'", {"key": dict(N, x={"label": "온도 (°C)", "label_size": 12})}, ""),
    ("A9", "axes", "paper", "tick number format (decimals, units)", "y2 틱 소수 한 자리",
     {"code": dict(N, code="from matplotlib.ticker import FormatStrFormatter\nax2.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))"),
      "partial_ec": dict(N, echarts={"yAxis": [{}, {"axisLabel": {"formatter": "{value} %/°C"}}]})},
     "ECharts: string templates can add text around the value but cannot set decimals"),
    ("A10", "axes", "tga", "second x axis (time on top)", "위쪽에 시간 축",
     {"code": dict(N, code="sec = ax1.secondary_xaxis('top', functions=(lambda T: (T - 30) / 10, lambda t: t * 10 + 30))\nsec.set_xlabel('Time (min)')"),
      "blocked_ec": dict(N, echarts={"xAxis": [{}, {"position": "top"}]})}, "ECharts patch: xAxis is a single object"),
    ("A11", "axes", "tga", "axis in other units (°C -> K)", "켈빈으로",
     {"code": dict(N, code="ax1.set_xticks(ax1.get_xticks()); ax1.set_xticklabels([f'{t + 273.15:.0f}' for t in ax1.get_xticks()])\nax1.set_xlabel('Temperature (K)')")},
     "ECharts: needs a formatter function; the allowlist rejects functions"),
    ("A12", "axes", "paper", "axis break", "y축 중간 생략", {}, "not practical in either engine without a second axes"),
    ("A13", "axes", "guide", "no right axis", "y2 없이", {"key": dict(N, y2=False)}, ""),
    ("A14", "axes", "lib", "rotated tick numbers", "x축 숫자 45도",
     {"code": dict(N, code="ax1.tick_params(axis='x', rotation=45)"),
      "echarts": dict(N, echarts={"xAxis": {"axisLabel": {"rotate": 45}}})}, ""),
    # ---- lines and markers
    ("L1", "lines", "guide", "line colour / width / style", "y1 선 초록 굵기 2 점선",
     {"key": dict(N, y1={"color": "green", "width": 2, "linestyle": "dotted"})}, ""),
    ("L2", "lines", "lib", "markers or scatter", "점으로", {"key": dict(N, y1={"style": "line+marker"}, y2={"style": "scatter"})},
     "ECharts legend shows no marker symbol"),
    ("L3", "lines", "tga", "colour per sample when overlaid", "Raw는 검정, ...",
     {"code": {"file": B + "cnt_batches.xlsx", "combine": True,
               "code": "for l, c in zip(ax1.get_lines()[:3], ['black', 'blue', 'red']): l.set_color(c)"},
      "echarts": {"file": B + "cnt_batches.xlsx", "combine": True,
                  "echarts": {"series": [{"lineStyle": {"color": "black"}}, {"lineStyle": {"color": "blue"}}, {"lineStyle": {"color": "red"}}]}}}, ""),
    ("L4", "lines", "paper", "fill under the curve", "무게 곡선 아래 칠하기",
     {"code": dict(N, code="ax1.fill_between(x, y1, alpha=0.1)"), "echarts": dict(N, echarts={"series": [{"areaStyle": {"opacity": 0.1}}]})}, ""),
    ("L5", "lines", "tga", "smoothed DTG", "DTG 부드럽게",
     {"code": dict(N, code="from scipy.signal import savgol_filter\nax2.get_lines()[0].set_ydata(savgol_filter(y2, 31, 3))"),
      "partial_ec": dict(N, echarts={"series": [{}, {"smooth": True}]})},
     "ECharts smooth only bends the drawn line between points; it does not filter noise"),
    ("L6", "lines", "paper", "error bars / spread band", "편차 표시", {"code": dict(N, code="ax1.fill_between(x, y1 - 1, y1 + 1, alpha=0.2)")},
     "needs the spread in the data; ECharts patch cannot add data"),
    ("L7", "lines", "tga", "offset (stacked) curves", "20%씩 띄워서",
     {"code": {"file": B + "polymers.xlsx", "combine": True, "y2": False,
               "code": "for i, l in enumerate(ax1.get_lines()[:3]): l.set_ydata(l.get_ydata() + 20 * i)\nax1.relim(); ax1.autoscale_view()"}},
     "ECharts patch cannot change data"),
    # ---- annotations and analysis
    ("N1", "annotate", "guide", "residue at a temperature", "잔류량 700 °C", {"key": dict(N, annotate={"residue": {"x": 700}})}, ""),
    ("N2", "annotate", "guide", "DTG peak labels", "피크 2개", {"key": dict(N, annotate={"peak": {"count": 2}})}, ""),
    ("N3", "annotate", "tga", "value at any x", "300 °C 무게", {"key": dict(N, annotate={"w": {"type": "value_at_x", "x": 300}})}, ""),
    ("N4", "annotate", "guide", "reference line", "450 °C 세로선", {"key": dict(N, annotate={"v": {"type": "vline", "x": 450, "text": "450"}})}, ""),
    ("N5", "annotate", "tga", "shaded range", "300~450 칠하기", {"key": dict(N, annotate={"b": {"type": "band", "x_min": 300, "x_max": 450}})}, ""),
    ("N6", "annotate", "paper", "free text note", "메모", {"key": dict(N, annotate={"t": {"type": "text", "text": "Air, 10 °C/min"}})}, ""),
    ("N7", "annotate", "paper", "arrow with text", "화살표",
     {"code": dict(N, code="ax1.annotate('oxidation', xy=(600, 50), xytext=(350, 30), arrowprops=dict(arrowstyle='->'))"),
      "echarts": dict(N, echarts={"series": [{"markLine": {"symbol": ["none", "arrow"], "label": {"formatter": "oxidation"},
                                                            "data": [[{"coord": [350, 30]}, {"coord": [600, 50]}]]}}]})},
     "ECharts puts the text at the arrow head, matplotlib at the tail"),
    ("N8", "annotate", "tga", "onset temperature", "onset 표시",
     {"code": dict(N, code="d = np.gradient(y1, x); k = int(np.argmin(d)); t = x[k] + (98 - y1[k]) / d[k]\nax1.axvline(t, ls=':'); ax1.text(t, 50, f'onset {t:.0f} °C')")},
     "ECharts: a number computed from the data cannot be produced by a patch"),
    ("N9", "annotate", "tga", "mass loss between two temperatures", "200~400 °C 감소량",
     {"code": dict(N, code="w = lambda T: y1[np.argmin(abs(x - T))]\nax1.text(250, 60, f'-{w(200) - w(400):.1f}%')")}, "same as N8"),
    ("N10", "annotate", "tga", "normalise (dry basis)", "150 °C 기준 100%",
     {"code": dict(N, code="ax1.get_lines()[0].set_ydata(y1 / y1[np.argmin(abs(x - 150))] * 100); ax1.relim(); ax1.autoscale_view()")},
     "ECharts patch cannot change data"),
    ("N11", "annotate", "tga", "DTG computed from the weight", "DTG 계산해서",
     {"code": {"file": B + "isothermal.txt", "preset": "none", "x": {"col": "B"}, "y1": {"col": "C"}, "y2": False,
               "code": "a2 = ax1.twinx(); a2.plot(x, -np.gradient(y1, x), color='#c0392b')"}}, "same as N10"),
    ("N12", "annotate", "tga", "endo/exo peaks on heat flow", "흡열 피크",
     {"key": {"file": B + "caox.csv", "y2": {"col": "E", "flip": "none"},
              "annotate": {"peak": False, "endo": {"type": "peak", "on": "y2", "kind": "min", "count": 2}}}}, ""),
    ("N13", "annotate", "guide", "label wording / decimals", "Residue: {}%", {"key": dict(N, annotate={"residue": {"text": "Residue {y:.2f}%"}})}, ""),
    ("N14", "annotate", "tga", "peaks only inside a range", "400~700 사이 피크", {"key": dict(N, annotate={"peak": {"x_min": 400, "x_max": 700}})}, ""),
    # ---- text and style
    ("S1", "style", "guide", "title text/size/colour", "제목 'CNT'", {"key": dict(N, title={"text": "CNT", "size": 16, "color": "navy"})}, ""),
    ("S2", "style", "guide", "all text one colour", "글자 회색", {"key": dict(N, text_color="gray")}, ""),
    ("S3", "style", "guide", "font size", "글자 13", {"key": dict(N, font_size=13)}, ""),
    ("S4", "style", "guide", "font family", "글꼴 Arial", {"key": dict(N, font="DejaVu Serif")}, ""),
    ("S5", "style", "paper", "bold text", "제목 굵게",
     {"code": dict(N, code="ax1.title.set_fontweight('bold')"), "echarts": dict(N, echarts={"title": {"textStyle": {"fontWeight": "bold"}}})}, ""),
    ("S6", "style", "paper", "background colour", "배경 연회색",
     {"code": dict(N, code="ax1.set_facecolor('#f5f5f5')"), "echarts": dict(N, echarts={"grid": {"backgroundColor": "#f5f5f5"}})}, ""),
    ("S7", "style", "guide", "grid", "격자", {"key": dict(N, grid=True)}, ""),
    ("S8", "style", "paper", "no frame / top line off", "테두리 없애기",
     {"code": dict(N, code="ax1.spines['top'].set_visible(False); ax2.spines['top'].set_visible(False)"),
      "partial_ec": dict(N, echarts={"grid": {"show": False}})}, "ECharts can drop the whole frame but not one side"),
    # ---- legend
    ("G1", "legend", "guide", "legend position (inside)", "범례 오른쪽 위", {"key": dict(N, legend="upper right")}, ""),
    ("G2", "legend", "guide", "legend off", "범례 없애기", {"key": dict(N, legend="none")}, ""),
    ("G3", "legend", "guide", "legend text size", "범례 9", {"key": dict(N, legend={"size": 9})}, ""),
    ("G4", "legend", "paper", "legend outside the plot", "범례 바깥",
     {"code": dict(N, code="h, l = [], []\nfor a in (ax1, ax2):\n    hh, ll = a.get_legend_handles_labels(); h += hh; l += ll\nax1.get_legend().remove(); fig.legend(h, l, loc='upper center', ncol=2, frameon=False); fig.subplots_adjust(top=0.82)"),
      "echarts": dict(N, echarts={"legend": {"left": None, "right": 4, "top": "middle", "orient": "vertical"}, "grid": {"right": 220}})}, ""),
    ("G5", "legend", "guide", "legend entry names", "범례 이름 '무게'", {"key": dict(N, y1={"legend": "무게"})}, ""),
    # ---- layout
    ("Y1", "layout", "tga", "two panels (weight above, DTG below)", "위아래로 나눠서",
     {"code": dict(N, code="fig.clear()\na, b = fig.subplots(2, 1, sharex=True)\na.plot(x, y1); b.plot(x, y2)")},
     "ECharts patch allows one grid"),
    ("Y2", "layout", "paper", "inset zoom", "확대 그림 넣기",
     {"code": dict(N, code="ins = ax1.inset_axes([0.55, 0.5, 0.4, 0.4]); ins.plot(x, y1); ins.set_xlim(150, 250); ins.set_ylim(96, 100)")},
     "ECharts patch allows one grid"),
    ("Y3", "layout", "guide", "figure size / dpi", "8×5, 600 dpi", {"key": dict(N, size=[8, 5], dpi=600)}, ""),
    ("Y4", "layout", "paper", "margins / aspect", "여백 줄이기",
     {"code": dict(N, code="fig.subplots_adjust(left=0.08, right=0.9)"), "echarts": dict(N, echarts={"grid": {"left": 50, "right": 60}})}, ""),
    # ---- output
    ("O1", "output", "guide", "file format", "pdf로", {"key": dict(N, output={"format": "svg"})}, ""),
    ("O2", "output", "guide", "several formats", "png랑 pdf", {"key": dict(N, output={"format": ["png", "svg"]})}, ""),
    ("O3", "output", "lib", "output folder / file name", "파일 이름", {"key": dict(N, output={"name": "{file}_{sheet}_v2"})}, ""),
    ("O4", "output", "paper", "transparent background", "배경 투명",
     {"code": dict(N, code="fig.patch.set_alpha(0); ax1.patch.set_alpha(0)"),
      "echarts": dict(N, echarts={"backgroundColor": "transparent"})}, "ECharts PNG is flattened onto white by the renderer"),
]


def try_draw(spec, engine, tag):
    s = json.loads(json.dumps(spec))
    f = s["file"]
    s["file"] = [str(paths.datapath(x)) for x in f] if isinstance(f, list) else str(paths.datapath(f))
    s["output"] = {**s.get("output", {}), "dir": str(HERE / "results" / "coverage" / tag / engine)}
    try:
        facts.plotkit_facts(s, engine, HERE / "results" / "coverage" / f"dump_{tag}.json")
        return "ok", ""
    except plotkit.PlotkitError as e:
        return "refused", f"{e.message} | {e.hint}"[:300]
    except Exception as e:
        return "error", repr(e)[:300]


def main():
    rows = []
    for iid, group, src, wish, example, routes, note in ITEMS:
        mpl = ec = "none"
        detail = []
        if "key" in routes:
            a, wa = try_draw(routes["key"], "matplotlib", iid + "_key")
            b, wb = try_draw(routes["key"], "echarts", iid + "_key")
            mpl = "key" if a == "ok" else f"key:{a}"
            ec = "key" if b == "ok" else f"key:{b}"
            detail += [w for w in (wa, wb) if w]
        if "code" in routes and mpl == "none":
            a, wa = try_draw(routes["code"], "matplotlib", iid + "_code")
            mpl = "code" if a == "ok" else f"code:{a}"
            detail += [wa] if wa else []
        for k, label in (("echarts", "echarts"), ("partial_ec", "partial")):
            if k in routes and ec == "none":
                b, wb = try_draw(routes[k], "echarts", iid + "_" + k)
                ec = label if b == "ok" else f"{label}:{b}"
                detail += [wb] if wb else []
        if "blocked_ec" in routes:
            b, wb = try_draw(routes["blocked_ec"], "echarts", iid + "_blocked")
            detail.append(f"tried ECharts patch -> {b}: {wb[:120]}")
        rows.append({"id": iid, "group": group, "source": src, "wish": wish, "example": example,
                     "matplotlib": mpl, "echarts": ec, "note": note, "detail": " || ".join(detail)})
        print(f"{iid:4s} {group:9s} {wish[:42]:42s} mpl={mpl:10s} ec={ec:10s}")
    p = HERE / "results" / "coverage.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    summ = {"items": len(rows), "matplotlib": dict(Counter(r["matplotlib"] for r in rows)),
            "echarts": dict(Counter(r["echarts"] for r in rows)),
            "by_group": {g: {"n": sum(r["group"] == g for r in rows),
                             "key": sum(r["group"] == g and r["matplotlib"] == "key" for r in rows)}
                         for g in dict.fromkeys(r["group"] for r in rows)}}
    (HERE / "results" / "coverage_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
