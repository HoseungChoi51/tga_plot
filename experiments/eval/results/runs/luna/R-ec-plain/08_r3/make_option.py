import json
import os
import re

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_number(value):
    try:
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def safe_name(text):
    name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text)).strip("_")
    return name or "plot"


figures = []

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
for sheet_name, df in sheets.items():
    df.columns = [str(column).strip() for column in df.columns]

    def find_column(fragment):
        for column in df.columns:
            if fragment.lower() in column.lower():
                return column
        return None

    x_col = find_column("temperature")
    weight_col = find_column("weight")
    derivative_col = find_column("d.w")

    if x_col is None or weight_col is None or derivative_col is None:
        continue

    data = df[[x_col, weight_col, derivative_col]].copy()
    for column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=[x_col, weight_col, derivative_col])

    weight_points = [
        [clean_number(x), clean_number(y)]
        for x, y in zip(data[x_col], data[weight_col])
    ]
    derivative_points = [
        [clean_number(x), clean_number(y)]
        for x, y in zip(data[x_col], data[derivative_col])
    ]

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "data": ["무게 (%)", "미분 무게 (%/°C)"],
            "top": 42,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 78, "right": 82, "top": 86, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "무게 (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "미분 무게 (%/°C)",
                "nameLocation": "middle",
                "nameGap": 60,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "무게 (%)",
                "type": "line",
                "data": weight_points,
                "showSymbol": False,
                "yAxisIndex": 0,
                "lineStyle": {"width": 2, "color": "#2563eb"},
                "itemStyle": {"color": "#2563eb"},
            },
            {
                "name": "미분 무게 (%/°C)",
                "type": "line",
                "data": derivative_points,
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {"width": 1.8, "color": "#dc2626"},
                "itemStyle": {"color": "#dc2626"},
            },
        ],
    }

    figures.append(
        {
            "name": safe_name(sheet_name),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
