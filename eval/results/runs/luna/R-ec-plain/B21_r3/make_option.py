import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
valid = temperature.notna() & weight.notna()

data = [
    [float(x), float(y)]
    for x, y in zip(temperature[valid], weight[valid])
]

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "title": {
        "text": "Raw",
        "left": "center",
        "textStyle": {"fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 74, "right": 28, "top": 64, "bottom": 64},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "inverse": True,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontSize": 12},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 48,
        "min": 0,
        "max": 105,
        "axisLabel": {"fontSize": 12},
        "splitLine": {"lineStyle": {"color": "#dddddd"}},
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#2878B5"},
        }
    ],
}

print(json.dumps({
    "figures": [{
        "name": "raw_weight",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
