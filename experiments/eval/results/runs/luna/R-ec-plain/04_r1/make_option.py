import json
import os
import sys

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

rows = [
    (float(x), float(y), float(d))
    for x, y, d in zip(temperature, weight, derivative)
    if pd.notna(x) and pd.notna(y) and pd.notna(d)
]

option = {
    "title": {
        "text": "CNT 산화 거동",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 18,
            "color": "navy",
            "fontWeight": "normal",
        },
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Weight(%)", "D.W(%/C)"],
        "top": 34,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "grid": {"left": 72, "right": 76, "top": 82, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "position": "right",
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 0,
            "data": [[x, y] for x, y, _ in rows],
            "lineStyle": {"width": 2, "color": "#1f77b4"},
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 1,
            "data": [[x, d] for x, _, d in rows],
            "lineStyle": {"width": 2, "color": "#d62728"},
        },
    ],
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "plot1",
                    "option": option,
                    "width": 614,
                    "height": 442,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
