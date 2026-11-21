import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PVC")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)
derivative = derivative[valid].to_numpy(dtype=float)

# Positive mass-loss rate is easier to interpret in the usual DTG convention.
dtg = -derivative

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "fontSize": 16,
        "color": "#222222"
    },
    "title": {
        "text": "PVC 열중량 분석 (TGA/DTG)",
        "left": "center",
        "top": 14,
        "textStyle": {"fontSize": 24, "fontWeight": "bold"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": None
    },
    "legend": {
        "top": 54,
        "data": ["중량", "질량 감소 속도 (DTG)"],
        "textStyle": {"fontSize": 16}
    },
    "grid": {
        "left": 90,
        "right": 105,
        "top": 105,
        "bottom": 78
    },
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontSize": 16},
        "nameTextStyle": {"fontSize": 16},
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "중량 (%)",
            "nameLocation": "middle",
            "nameGap": 55,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#2463a6"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
        },
        {
            "type": "value",
            "name": "질량 감소 속도 (%/°C)",
            "nameLocation": "middle",
            "nameGap": 70,
            "min": 0,
            "max": 1.15,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#c44e52"}},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "중량",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 3, "color": "#2463a6"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)]
        },
        {
            "name": "질량 감소 속도 (DTG)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 3, "color": "#c44e52"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, dtg)]
        }
    ]
}

# Remove unsupported/unused formatter field while keeping the option plain JSON.
option["tooltip"].pop("valueFormatter", None)

result = {
    "figures": [
        {
            "name": "pvc_tga",
            "option": option,
            "width": 960,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result, ensure_ascii=False, allow_nan=False))
