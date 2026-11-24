import json
import math
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

FONT = "Noto Sans CJK KR"
GRAY_FILL = "#dcdcdc"  # 연한 회색
SHADED_LO = 300.0
SHADED_HI = 450.0

COL_WEIGHT = "#1f4e9c"
COL_DTG = "#c0392b"


def clean_num(v):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def round_sig(v, n=4):
    if v is None:
        return None
    return float(f"{v:.{n}g}")


def build_figure(sheet_name, df):
    # column identification
    cols = list(df.columns)
    x_col = y1_col = y2_col = None
    for c in cols:
        lc = str(c).lower()
        if x_col is None and ("temp" in lc or "온도" in lc):
            x_col = c
        if y1_col is None and "weight" in lc and "d" not in lc.replace("weight", ""):
            if "d.w" not in lc and "dtg" not in lc and "d.w" not in lc:
                y1_col = c
        if y2_col is None and ("d.w" in lc or "dtg" in lc or "deriv" in lc):
            y2_col = c
    if x_col is None:
        x_col = cols[1]
    if y1_col is None:
        y1_col = cols[2]
    if y2_col is None:
        y2_col = cols[3]

    data = df[[x_col, y1_col, y2_col]].dropna()
    x = data[x_col].astype(float).tolist()
    w = data[y1_col].astype(float).tolist()
    dtg = data[y2_col].astype(float).tolist()
    dtg_neg = [-v for v in dtg]

    pts_w = [[round_sig(a), round_sig(b)] for a, b in zip(x, w)]
    pts_d = [[round_sig(a), round_sig(b)] for a, b in zip(x, dtg_neg)]

    # residue: weight at measured point nearest 800 C
    idx_res = min(range(len(x)), key=lambda i: abs(x[i] - 800.0))
    res_t, res_w = x[idx_res], w[idx_res]
    res_label = "Residue {:.1f}%".format(res_w)

    # peak: highest DTG peak above 150 C (using inverted DTG)
    peak_t = None
    peak_v = None
    for i in range(len(x)):
        if x[i] > 150.0:
            if peak_v is None or dtg_neg[i] > peak_v:
                peak_v = dtg_neg[i]
                peak_t = x[i]
    peak_label = "{:.0f} °C".format(peak_t) if peak_t is not None else ""

    # axis ranges
    x_min, x_max = min(x), max(x)
    w_min, w_max = min(w), max(w)
    d_min, d_max = min(dtg_neg), max(dtg_neg)

    mark_area = {
        "silent": True,
        "label": {"show": False},
        "itemStyle": {
            "color": GRAY_FILL,
            "opacity": 0.55,
            "borderWidth": 0,
        },
        "data": [[{"xAxis": SHADED_LO}, {"xAxis": SHADED_HI}]],
    }

    residue_mark = {
        "symbol": "circle",
        "symbolSize": 9,
        "itemStyle": {"color": COL_WEIGHT, "borderColor": "#ffffff", "borderWidth": 1},
        "label": {
            "show": True,
            "formatter": res_label,
            "position": "top",
            "color": COL_WEIGHT,
            "fontSize": 11,
            "fontWeight": "bold",
            "fontFamily": FONT,
        },
        "data": [{"coord": [round_sig(res_t), round_sig(res_w)]}],
    }

    peak_mark = {
        "symbol": "triangle",
        "symbolSize": 10,
        "itemStyle": {"color": COL_DTG, "borderColor": "#ffffff", "borderWidth": 1},
        "label": {
            "show": True,
            "formatter": peak_label,
            "position": "top",
            "color": COL_DTG,
            "fontSize": 11,
            "fontWeight": "bold",
            "fontFamily": FONT,
        },
        "data": [{"coord": [round_sig(peak_t), round_sig(peak_v)]}] if peak_t is not None else [],
    }

    option = {
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": FONT},
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 8,
            "textStyle": {"fontSize": 14, "fontFamily": FONT},
        },
        "legend": {
            "left": "left",
            "top": "middle",
            "orient": "vertical",
            "textStyle": {"fontFamily": FONT, "fontSize": 11},
            "data": ["Weight (%)", "DTG (×-1)"],
        },
        "grid": {"left": 70, "right": 70, "top": 50, "bottom": 55},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"fontFamily": FONT, "fontSize": 12},
            "min": round_sig(x_min),
            "max": round_sig(x_max),
            "axisLabel": {"fontFamily": FONT, "fontSize": 10},
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "nameTextStyle": {"fontFamily": FONT, "fontSize": 12, "color": COL_WEIGHT},
                "min": round_sig(min(0.0, w_min)),
                "max": round_sig(max(100.0, w_max)),
                "axisLabel": {"fontFamily": FONT, "fontSize": 10},
                "axisLine": {"show": True, "lineStyle": {"color": COL_WEIGHT}},
                "axisTick": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
            },
            {
                "type": "value",
                "name": "DTG (×-1)",
                "nameLocation": "middle",
                "nameGap": 40,
                "nameTextStyle": {"fontFamily": FONT, "fontSize": 12, "color": COL_DTG},
                "min": round_sig(min(0.0, d_min)),
                "max": round_sig(max(0.0, d_max)),
                "axisLabel": {"fontFamily": FONT, "fontSize": 10},
                "axisLine": {"show": True, "lineStyle": {"color": COL_DTG}},
                "axisTick": {"show": True},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {"color": COL_WEIGHT, "width": 1.6},
                "itemStyle": {"color": COL_WEIGHT},
                "data": pts_w,
                "markArea": mark_area,
                "markPoint": residue_mark,
            },
            {
                "name": "DTG (×-1)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {"color": COL_DTG, "width": 1.4},
                "itemStyle": {"color": COL_DTG},
                "data": pts_d,
                "markPoint": peak_mark,
            },
        ],
    }
    return option


def main():
    xls = pd.ExcelFile(DATA_FILE)
    figures = []
    for i, sheet in enumerate(xls.sheet_names):
        df = pd.read_excel(DATA_FILE, sheet_name=sheet, header=0)
        option = build_figure(sheet, df)
        figures.append({
            "name": "plot{}".format(i + 1),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })
    print(json.dumps({"figures": figures}, ensure_ascii=False))


if __name__ == "__main__":
    main()
