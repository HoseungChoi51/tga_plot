import json
import re
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PVC")
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    raise ValueError(f"필수 열을 찾을 수 없습니다: {pattern}")

temp_col = find_column(r"Temperature")
weight_col = find_column(r"Weight\s*\(%\)")
deriv_col = find_column(r"Deriv")

data = pd.DataFrame({
    "temperature": pd.to_numeric(df[temp_col], errors="coerce"),
    "weight": pd.to_numeric(df[weight_col], errors="coerce"),
    "derivative": pd.to_numeric(df[deriv_col], errors="coerce"),
}).dropna()

temperature = data["temperature"].to_numpy()
weight = data["weight"].to_numpy()
derivative = data["derivative"].to_numpy()

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "fontSize": 16,
        "color": "#222222"
    },
    "title": {
        "text": "PVC 열중량 분석 (TGA)",
        "left": "center",
        "top": 16,
        "textStyle": {"fontSize": 23, "fontWeight": "bold"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "textStyle": {"fontSize": 16}
    },
    "legend": {
        "data": ["중량", "미분 중량"],
        "top": 56,
        "textStyle": {"fontSize": 16}
    },
    "grid": {"left": 88, "right": 92, "top": 108, "bottom": 80},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 48,
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
            "nameGap": 58,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#2878b5"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
        },
        {
            "type": "value",
            "name": "미분 중량 (%/°C)",
            "nameLocation": "middle",
            "nameGap": 64,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#d65f28"}},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "중량",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 3, "color": "#2878b5"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)]
        },
        {
            "name": "미분 중량",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 3, "color": "#d65f28"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, derivative)]
        }
    ]
}

figure = {
    "name": "pvc_tga",
    "option": option,
    "width": 960,
    "height": 600,
    "dpi": 300,
    "formats": ["png"]
}

print(json.dumps({"figures": [figure]}, ensure_ascii=False, allow_nan=False))
