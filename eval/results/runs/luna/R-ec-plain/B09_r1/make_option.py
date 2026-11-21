import json
import os
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def main():
    df = pd.read_excel(DATA_FILE, sheet_name="PE")
    temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
    derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

    weight_data = []
    derivative_data = []
    for x, y1, y2 in zip(temperature, weight, derivative):
        if pd.notna(x):
            weight_data.append([float(x), float(y1) if pd.notna(y1) else None])
            derivative_data.append([float(x), float(y2) if pd.notna(y2) else None])

    option = {
        "animation": False,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR, sans-serif"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
            "top": 10
        },
        "grid": {
            "left": 78,
            "right": 82,
            "top": 55,
            "bottom": 68
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 100,
            "max": 700,
            "interval": 100,
            "axisLabel": {"showMinLabel": True, "showMaxLabel": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": 0,
                "max": 100,
                "axisLine": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "nameLocation": "middle",
                "nameGap": 58,
                "position": "right",
                "axisLine": {"show": True},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": weight_data,
                "yAxisIndex": 0,
                "showSymbol": False,
                "connectNulls": False,
                "lineStyle": {"color": "#ff0000", "width": 3},
                "itemStyle": {"color": "#ff0000"}
            },
            {
                "name": "Deriv. Weight (%/°C)",
                "type": "line",
                "data": derivative_data,
                "yAxisIndex": 1,
                "showSymbol": False,
                "connectNulls": False,
                "lineStyle": {"color": "#2878b5", "width": 1.5},
                "itemStyle": {"color": "#2878b5"}
            }
        ]
    }

    result = {
        "figures": [
            {
                "name": "PE",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"]
            }
        ]
    }
    json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False)

if __name__ == "__main__":
    main()
