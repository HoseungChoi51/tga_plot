import json
import math
import os

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

colors = {
    "PE": "#1f77b4",
    "PVC": "#d62728",
    "PET": "#2ca02c",
}

series = []
for sheet_name in ("PE", "PVC", "PET"):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
    valid = temperature.notna() & weight.notna()

    # Offset each curve by 20 percentage points to keep the curves separated.
    offset = {"PE": 40, "PVC": 20, "PET": 0}[sheet_name]
    data = [
        [float(x), float(y + offset)]
        for x, y in zip(temperature[valid], weight[valid])
        if math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    series.append({
        "name": f"{sheet_name} (+{offset}%)" if offset else sheet_name,
        "type": "line",
        "showSymbol": False,
        "connectNulls": False,
        "lineStyle": {"width": 2, "color": colors[sheet_name]},
        "itemStyle": {"color": colors[sheet_name]},
        "data": data,
    })

option = {
    "animation": False,
    "title": {
        "text": "TGA 무게 곡선",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "line"},
    },
    "legend": {
        "top": 32,
        "data": ["PE (+40%)", "PVC (+20%)", "PET"],
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "grid": {"left": 78, "right": 28, "top": 82, "bottom": 65},
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
    "yAxis": {
        "type": "value",
        "name": "Weight (%) — offset 적용",
        "nameLocation": "middle",
        "nameGap": 55,
        "min": 0,
        "max": 160,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#dddddd"}},
    },
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "tga_weight_offset",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
