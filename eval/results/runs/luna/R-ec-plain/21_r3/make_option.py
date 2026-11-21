import json
import os
import sys

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=7, usecols="C:E")
df.columns = ["Temperature", "Weight(%)", "D.W(%/C)"]

for column in df.columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")
df = df.dropna(subset=["Temperature", "Weight(%)", "D.W(%/C)"])

temperature = df["Temperature"].tolist()
weight = df["Weight(%)"].tolist()
derivative = df["D.W(%/C)"].tolist()

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Weight(%)", "D.W(%/C)"],
        "top": 10,
    },
    "grid": {
        "left": 76,
        "right": 82,
        "top": 58,
        "bottom": 68,
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "axisLabel": {"formatter": "{value}"},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLine": {"show": True},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#2563eb"},
            "itemStyle": {"color": "#2563eb"},
            "data": [[x, y] for x, y in zip(temperature, weight)],
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#dc2626"},
            "itemStyle": {"color": "#dc2626"},
            "data": [[x, y] for x, y in zip(temperature, derivative)],
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "tga_weight_derivative",
        "option": option,
        "width": 900,
        "height": 600,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
