import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")

valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()

data = [[float(x), float(y)] for x, y in zip(temperature, weight)]

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
    "title": {
        "text": "Raw",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 16, "fontWeight": "normal", "color": "#222"}
    },
    "grid": {"left": 76, "right": 32, "top": 64, "bottom": 64},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#444"},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 48,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#444"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}}
    },
    "graphic": [{
        "type": "text",
        "right": 34,
        "top": 23,
        "style": {
            "text": "공기, 10 °C/min",
            "font": "14px Noto Sans CJK KR",
            "fill": "#333"
        }
    }],
    "series": [{
        "name": "Weight (%)",
        "type": "line",
        "data": data,
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": "#2878b5"},
        "itemStyle": {"color": "#2878b5"},
        "markLine": {
            "silent": True,
            "symbol": ["none", "none"],
            "lineStyle": {"color": "#d9534f", "width": 1.5, "type": "dashed"},
            "label": {
                "show": True,
                "formatter": "50%",
                "position": "insideEndTop",
                "color": "#d9534f"
            },
            "data": [{"yAxis": 50}]
        }
    }]
}

print(json.dumps({
    "figures": [{
        "name": "raw_tga",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
