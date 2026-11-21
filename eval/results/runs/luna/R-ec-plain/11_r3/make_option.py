import json
import os

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#2878B5", "#D9534F", "#3A9D5D"]
FIGURES = []

for sheet_index, sheet_name in enumerate(pd.ExcelFile(DATA_FILE).sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next((c for c in df.columns if "temperature" in c.lower()), None)
    weight_col = next((c for c in df.columns if "weight" in c.lower()), None)
    derivative_col = next(
        (c for c in df.columns if "d.w" in c.lower() or "derivative" in c.lower()),
        None,
    )
    if temperature_col is None or weight_col is None:
        continue

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid = temperature.notna() & weight.notna()

    series = [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "symbol": "none",
            "data": [
                [round(float(x), 6), round(float(y), 6)]
                for x, y in zip(temperature[valid], weight[valid])
            ],
            "lineStyle": {"width": 2, "color": COLORS[sheet_index % len(COLORS)]},
            "itemStyle": {"color": COLORS[sheet_index % len(COLORS)]},
            "yAxisIndex": 0,
        }
    ]

    if derivative_col is not None:
        derivative = pd.to_numeric(df[derivative_col], errors="coerce")
        valid_derivative = temperature.notna() & derivative.notna()
        series.append(
            {
                "name": "D.W",
                "type": "line",
                "showSymbol": False,
                "symbol": "none",
                "data": [
                    [round(float(x), 6), round(float(y), 6)]
                    for x, y in zip(
                        temperature[valid_derivative], derivative[valid_derivative]
                    )
                ],
                "lineStyle": {"width": 1.5, "color": "#777777"},
                "itemStyle": {"color": "#777777"},
                "yAxisIndex": 1,
            }
        )

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 12,
            "textStyle": {"fontSize": 16, "fontWeight": "normal"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 40, "data": [s["name"] for s in series]},
        "grid": {"left": 78, "right": 78, "top": 82, "bottom": 66},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": float(temperature[valid].max()),
            "axisLine": {"lineStyle": {"color": "#555555"}},
            "splitLine": {"lineStyle": {"color": "#E6E6E6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": COLORS[sheet_index % len(COLORS)]}},
                "splitLine": {"lineStyle": {"color": "#E6E6E6"}},
            }
        ],
        "series": series,
    }

    if derivative_col is not None:
        option["yAxis"].append(
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 54,
                "axisLine": {"show": True, "lineStyle": {"color": "#777777"}},
                "splitLine": {"show": False},
            }
        )

    safe_name = "".join(
        ch if ch.isalnum() or ch in "-_" else "_" for ch in sheet_name
    ).strip("_")
    FIGURES.append(
        {
            "name": safe_name or f"plot{sheet_index + 1}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": FIGURES}, ensure_ascii=False, allow_nan=False))
