import json
import os
import re
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#1f4e9c", "#c0392b", "#2e8b57", "#8e44ad", "#d68910", "#117a8b"]
WIDTH, HEIGHT, DPI = 614, 442, 300


def clean_name(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_") or "plot"


def find_column(columns, pattern, fallback):
    for col in columns:
        if re.search(pattern, str(col), re.I):
            return col
    return columns[fallback] if len(columns) > fallback else None


def numeric_pairs(df, x_col, y_col):
    x = pd.to_numeric(df[x_col], errors="coerce")
    y = pd.to_numeric(df[y_col], errors="coerce")
    valid = x.notna() & y.notna()
    return x[valid].to_numpy(dtype=float), y[valid].to_numpy(dtype=float)


def main():
    path = DATA_FILE
    excel = pd.ExcelFile(path)
    series = []
    all_x = []
    all_weight = []
    all_dtg = []

    for i, sheet in enumerate(excel.sheet_names):
        df = pd.read_excel(path, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        cols = list(df.columns)

        x_col = find_column(cols, r"temperature|temp|온도", 1)
        weight_col = find_column(cols, r"weight|mass|중량|무게", 2)
        dtg_col = find_column(cols, r"d\.?\s*w|dtg|derivative|미분", 3)

        if x_col is None or weight_col is None or dtg_col is None:
            continue

        x, weight = numeric_pairs(df, x_col, weight_col)
        dx, dtg = numeric_pairs(df, x_col, dtg_col)
        if len(x) == 0 or len(dx) == 0:
            continue

        # Ensure each trace is ordered along temperature.
        order = np.argsort(x)
        x, weight = x[order], weight[order]
        order_dtg = np.argsort(dx)
        dx, dtg = dx[order_dtg], dtg[order_dtg]

        color = COLORS[i % len(COLORS)]
        series.append({
            "name": f"{sheet} Weight",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 0,
            "lineStyle": {"width": 2, "color": color},
            "itemStyle": {"color": color},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
        })
        series.append({
            "name": f"{sheet} DTG",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 1,
            "lineStyle": {"width": 1.6, "color": color, "type": "dashed"},
            "itemStyle": {"color": color},
            "data": [[float(a), float(-b)] for a, b in zip(dx, dtg)],
        })

        all_x.extend(x.tolist())
        all_weight.extend(weight.tolist())
        all_dtg.extend((-dtg).tolist())

        # Label the residue and the highest positive DTG peak above 150 °C
        # for each sheet, as on the standard TGA plot.
        residue_idx = int(np.argmin(np.abs(x - 800.0)))
        series.append({
            "name": f"{sheet} Residue",
            "type": "scatter",
            "yAxisIndex": 0,
            "symbolSize": 8,
            "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": f"Residue {weight[residue_idx]:.1f}%",
                "position": "right",
                "fontSize": 10,
                "color": color,
            },
            "data": [[float(x[residue_idx]), float(weight[residue_idx])]],
            "tooltip": {"show": False},
        })

        candidates = np.flatnonzero((dx > 150.0) & ((-dtg) > 0.0))
        if len(candidates):
            peak_idx = int(candidates[np.argmax((-dtg)[candidates])])
            series.append({
                "name": f"{sheet} Peak",
                "type": "scatter",
                "yAxisIndex": 1,
                "symbolSize": 8,
                "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"{dx[peak_idx]:.0f} °C",
                    "position": "top",
                    "fontSize": 10,
                    "color": color,
                },
                "data": [[float(dx[peak_idx]), float(-dtg[peak_idx])]],
                "tooltip": {"show": False},
            })

    if not series:
        raise ValueError("유효한 TGA 시트를 찾지 못했습니다.")

    x_min, x_max = float(min(all_x)), float(max(all_x))
    w_min, w_max = float(min(all_weight)), float(max(all_weight))
    d_min, d_max = float(min(all_dtg)), float(max(all_dtg))
    w_pad = max((w_max - w_min) * 0.06, 1.0)
    d_pad = max((d_max - d_min) * 0.08, 0.02)

    option = {
        "animation": False,
        "title": {
            "text": "TGA — all sheets",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 15},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "type": "scroll",
            "orient": "vertical",
            "left": 12,
            "top": "middle",
            "width": 140,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 9},
            "data": [s["name"] for s in series if s["type"] == "line"],
        },
        "grid": {"left": 165, "right": 70, "top": 55, "bottom": 55},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 32,
            "min": x_min,
            "max": x_max,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 45,
                "min": w_min - w_pad,
                "max": w_max + w_pad,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": "#1f4e9c"},
                "splitLine": {"show": False},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": min(0.0, d_min - d_pad),
                "max": d_max + d_pad,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": "#c0392b"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    result = {
        "figures": [{
            "name": clean_name(os.path.splitext(os.path.basename(path))[0] + "_overlay"),
            "option": option,
            "width": WIDTH,
            "height": HEIGHT,
            "dpi": DPI,
            "formats": ["png"],
        }]
    }
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


if __name__ == "__main__":
    main()
