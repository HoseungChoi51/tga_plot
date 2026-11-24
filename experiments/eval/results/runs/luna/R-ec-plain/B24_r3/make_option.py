import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PE")
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "temperature" in c.lower())
weight_col = next(c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower())

temperature_c = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature_c.notna() & weight.notna()

data = [
    [round(float(t) + 273.15, 4), round(float(w), 6)]
    for t, w in zip(temperature_c[valid], weight[valid])
]

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "title": {
        "text": "PE 열중량 분석 (TGA)",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 18, "fontWeight": "normal"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": "{value}"
    },
    "grid": {"left": 76, "right": 28, "top": 66, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "온도 (K)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 303.15,
        "max": 1173.15,
        "axisLabel": {"formatter": "{value}"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "yAxis": {
        "type": "value",
        "name": "질량 (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLabel": {"formatter": "{value}"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "series": [{
        "name": "PE",
        "type": "line",
        "data": data,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"width": 2, "color": "#2673b8"},
        "emphasis": {"focus": "series"}
    }]
}

print(json.dumps({
    "figures": [{
        "name": "pe_tga_kelvin",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
