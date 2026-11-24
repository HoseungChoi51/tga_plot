import json

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
derivative = derivative[valid].to_numpy()

option = {
    "animation": False,
    "title": {
        "text": "TGA — Raw",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 36,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "grid": {"left": 76, "right": 76, "top": 88, "bottom": 64},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "inverse": True,
        "min": float(np.nanmin(temperature)),
        "max": float(np.nanmax(temperature)),
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True},
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 54,
            "inverse": True,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#2563eb"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 1.6, "color": "#dc2626"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, derivative)],
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "raw_tga_temperature_reversed",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
