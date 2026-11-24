import json
import os
import re

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

excel = pd.ExcelFile(DATA_FILE)
colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]

series = []
for index, sheet_name in enumerate(excel.sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(
        (column for column in df.columns if "temperature" in column.lower()),
        None,
    )
    weight_col = next(
        (column for column in df.columns if "weight" in column.lower()),
        None,
    )
    if temperature_col is None or weight_col is None:
        continue

    data = []
    for x, y in zip(
        pd.to_numeric(df[temperature_col], errors="coerce"),
        pd.to_numeric(df[weight_col], errors="coerce"),
    ):
        if pd.notna(x) and pd.notna(y):
            data.append([float(x), float(y)])

    series.append(
        {
            "name": sheet_name,
            "type": "line",
            "data": data,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": colors[index % len(colors)]},
            "itemStyle": {"color": colors[index % len(colors)]},
            "emphasis": {"focus": "series"},
        }
    )

option = {
    "backgroundColor": "#ffffff",
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#334155"},
    "title": {
        "text": "TGA 시트별 열중량 곡선",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 18, "fontWeight": "bold", "color": "#0f172a"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": "{value}",
    },
    "legend": {
        "data": [item["name"] for item in series],
        "top": 48,
        "left": "center",
        "type": "scroll",
    },
    "grid": {"left": 78, "right": 34, "top": 96, "bottom": 66},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#64748b"}},
        "axisLabel": {"color": "#475569"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e2e8f0"}},
    },
    "yAxis": {
        "type": "value",
        "name": "중량 (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#64748b"}},
        "axisLabel": {"color": "#475569"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e2e8f0"}},
    },
    "series": series,
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "tga_overlaid",
                    "option": option,
                    "width": 900,
                    "height": 600,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
