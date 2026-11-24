import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"


def read_table(path):
    # Detect common text-file delimiters; fall back to whitespace-separated data.
    for sep in (None, r"\s+"):
        try:
            df = pd.read_csv(path, sep=sep, engine="python", comment="#")
            if df.shape[1] >= 3:
                return df
        except Exception:
            pass
    raise ValueError(f"Could not read data table: {path}")


def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip()).lower()


df = read_table(DATA_FILE)
names = {clean_name(col): col for col in df.columns}


def find_column(tokens, fallback_index):
    for normalized, original in names.items():
        if any(token in normalized for token in tokens):
            return original
    return df.columns[fallback_index]


time_col = find_column(("time", "시간"), 0)
temp_col = find_column(("temperature", "temp", "온도"), 1)
weight_col = find_column(("weight", "mass", "무게", "중량"), 2)

data = pd.DataFrame({
    "time": pd.to_numeric(df[time_col], errors="coerce"),
    "temperature": pd.to_numeric(df[temp_col], errors="coerce"),
    "weight": pd.to_numeric(df[weight_col], errors="coerce"),
}).dropna().sort_values("time")

if data.empty:
    raise ValueError("No numeric data rows found.")

x = data["time"].to_numpy(dtype=float)
weight = data["weight"].to_numpy(dtype=float)
temperature = data["temperature"].to_numpy(dtype=float)

target_time = 140.0
idx = int(np.argmin(np.abs(x - target_time)))
label_time = float(x[idx])
label_weight = float(weight[idx])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "color": "#333333",
    },
    "title": {
        "text": "Isothermal",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 18, "fontWeight": "normal"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Weight (%)", "Temperature (°C)"],
        "left": "center",
        "top": 44,
    },
    "grid": {"left": 76, "right": 76, "top": 92, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Time (min)",
        "nameLocation": "middle",
        "nameGap": 36,
        "min": 0,
        "max": 140,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "position": "left",
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"color": "#1f4e9c"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "position": "right",
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"color": "#c0392b"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"140 min: {label_weight:g}%",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontSize": 12,
                },
                "data": [{"coord": [label_time, label_weight]}],
            },
        },
        {
            "name": "Temperature (°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#c0392b"},
            "data": [[float(a), float(b)] for a, b in zip(x, temperature)],
        },
    ],
}

result = {
    "figures": [
        {
            "name": "isothermal",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
