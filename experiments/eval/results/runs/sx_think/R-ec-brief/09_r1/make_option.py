import json
import math
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

FONT = "Noto Sans CJK KR"
COLOR_W = "#1f4e9c"
COLOR_D = "#c0392b"
TICK_LABEL_SIZE = 9  # user: tick label size 9 -> applies to x, y1, y2


def find_col(columns, keywords, exclude=None):
    for kw in keywords:
        for c in columns:
            lc = str(c).lower()
            if kw in lc:
                if exclude and any(e in lc for e in exclude):
                    continue
                return c
    return None


def clean_series(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    return x[m], y[m]


def build_figure(name, sheet_name, df):
    cols = list(df.columns)
    xcol = find_col(cols, ["temp"])
    y1col = find_col(cols, ["weight"])
    y2col = find_col(cols, ["d.w", "dtg", "derivative", "dw"])

    if xcol is None or y1col is None or y2col is None:
        return None

    tx, wy = clean_series(df[xcol], df[y1col])
    td, dy = clean_series(df[y2col], df[y2col])
    dy = -dy  # flip DTG so peaks point up

    if len(tx) == 0 or len(td) == 0:
        return None

    # residue: weight at measured point nearest 800 C
    i_res = int(np.argmin(np.abs(tx - 800.0)))
    t_res, w_res = float(tx[i_res]), float(wy[i_res])

    # peak: highest (flipped) DTG peak above 150 C
    mask = td > 150.0
    if np.any(mask):
        t_pk = float(td[mask][np.argmax(dy[mask])])
        d_pk = float(dy[mask][np.max(np.where(mask, dy, -np.inf))])
    else:
        t_pk = float(td[np.argmax(dy)])
        d_pk = float(np.max(dy))

    weight_data = [[round(float(a), 4), round(float(b), 4)] for a, b in zip(tx, wy)]
    dtg_data = [[round(float(a), 4), round(float(b), 4)] for a, b in zip(td, dy)]

    tick = {"show": True, "inside": False, "length": 5, "lineStyle": {"color": "#333"}}
    label = {"show": True, "fontSize": TICK_LABEL_SIZE, "color": "#333"}

    option = {
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": FONT},
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 8,
            "textStyle": {"fontSize": 13, "fontWeight": "bold", "color": "#222", "fontFamily": FONT},
        },
        "legend": {
            "left": 12,
            "top": "middle",
            "orient": "vertical",
            "itemGap": 8,
            "textStyle": {"fontSize": 10, "color": "#333", "fontFamily": FONT},
            "data": ["Weight", "DTG"],
        },
        "grid": {"left": 70, "right": 70, "top": 55, "bottom": 55},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "value",
            "name": "Temperature (\u00b0C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"fontSize": 11, "color": "#333", "fontFamily": FONT},
            "axisTick": dict(tick),
            "axisLabel": dict(label),
            "axisLine": {"show": True, "lineStyle": {"color": "#333"}},
            "splitLine": {"show": False},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 40,
                "nameTextStyle": {"fontSize": 11, "color": COLOR_W, "fontFamily": FONT},
                "axisTick": dict(tick),
                "axisLabel": dict(label),
                "axisLine": {"show": True, "lineStyle": {"color": COLOR_W}},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "DTG (%/\u00b0C)",
                "nameLocation": "middle",
                "nameGap": 45,
                "nameTextStyle": {"fontSize": 11, "color": COLOR_D, "fontFamily": FONT},
                "axisTick": dict(tick),
                "axisLabel": dict(label),
                "axisLine": {"show": True, "lineStyle": {"color": COLOR_D}},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "lineStyle": {"color": COLOR_W, "width": 1.6},
                "itemStyle": {"color": COLOR_W},
                "data": weight_data,
            },
            {
                "name": "DTG",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "lineStyle": {"color": COLOR_D, "width": 1.6},
                "itemStyle": {"color": COLOR_D},
                "data": dtg_data,
            },
            {
                "name": "Residue",
                "type": "scatter",
                "yAxisIndex": 0,
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": COLOR_W, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "Residue {:.1f}%".format(w_res),
                    "fontSize": 10,
                    "fontWeight": "bold",
                    "color": COLOR_W,
                    "fontFamily": FONT,
                },
                "data": [[round(t_res, 2), round(w_res, 3)]],
                "tooltip": {"show": False},
            },
            {
                "name": "Peak",
                "type": "scatter",
                "yAxisIndex": 1,
                "symbol": "triangle",
                "symbolSize": 10,
                "itemStyle": {"color": COLOR_D, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{:.0f} \u00b0C".format(t_pk),
                    "fontSize": 10,
                    "fontWeight": "bold",
                    "color": COLOR_D,
                    "fontFamily": FONT,
                },
                "data": [[round(t_pk, 2), round(d_pk, 4)]],
                "tooltip": {"show": False},
            },
        ],
    }
    return option


def main():
    figures = []
    sheets = pd.read_excel(DATA_FILE, sheet_name=None, header=0)
    idx = 0
    for sheet_name, df in sheets.items():
        df = df.dropna(how="all")
        opt = build_figure("plot{}".format(idx + 1), sheet_name, df)
        if opt is not None:
            idx += 1
            figures.append({
                "name": "plot{}".format(idx),
                "option": opt,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            })
    print(json.dumps({"figures": figures}, ensure_ascii=False))


if __name__ == "__main__":
    main()
