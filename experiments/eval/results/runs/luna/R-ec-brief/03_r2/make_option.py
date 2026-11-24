import json
import os
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V acid"

def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip())

def main():
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    df.columns = [clean_name(c) for c in df.columns]

    def find_col(pattern):
        matches = [c for c in df.columns if re.search(pattern, c, re.I)]
        if not matches:
            raise ValueError(f"Cannot find column matching {pattern!r}")
        return matches[0]

    x_col = find_col(r"temperature|temp")
    weight_col = find_col(r"weight")
    dtg_col = find_col(r"D\.?\s*W|DTG|derivative")

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(x_col)
    x = data[x_col].to_numpy(dtype=float)
    weight = data[weight_col].to_numpy(dtype=float)
    dtg = data[dtg_col].to_numpy(dtype=float)

    # The requested peak markers show the two largest DTG peaks above 150 °C.
    peak_candidates = np.flatnonzero(x > 150)
    if peak_candidates.size:
        order = peak_candidates[np.argsort(dtg[peak_candidates])[::-1]]
        peak_indices = []
        for idx in order:
            # Avoid selecting adjacent points from the same peak.
            if all(abs(x[idx] - x[prev]) >= 15 for prev in peak_indices):
                peak_indices.append(int(idx))
            if len(peak_indices) == 2:
                break
        peak_indices.sort(key=lambda i: x[i])
    else:
        peak_indices = []

    series = [
        {
            "name": "Weight(%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
        },
    ]

    if peak_indices:
        peak_points = [
            {
                "coord": [float(x[i]), float(-dtg[i])],
                "value": f"{x[i]:.0f} °C",
                "label": {"show": True, "formatter": f"{x[i]:.0f} °C", "position": "top"},
            }
            for i in peak_indices
        ]
        series[1]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 10,
            "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1},
            "data": peak_points,
        }

    option = {
        "animation": False,
        "title": {
            "text": SHEET_NAME,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "color": "#222222"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight(%)", "-DTG (%/°C)"], "left": "center", "top": 34},
        "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": 100,
            "max": 800,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": "#333333"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": "#333333"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": "#333333"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    result = {
        "figures": [
            {
                "name": "1006R1-V_acid",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        ]
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
