import json
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"


def read_csv_with_fallback(path):
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin1")


df = read_csv_with_fallback(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

x_col = "온도(°C)"
weight_col = "무게(%)"
derivative_col = "미분무게(%/°C)"

for col in (x_col, weight_col, derivative_col):
    if col not in df.columns:
        raise ValueError(f"필수 열을 찾을 수 없습니다: {col}")

for col in (x_col, weight_col, derivative_col):
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[x_col, weight_col, derivative_col])
if df.empty:
    raise ValueError("그래프를 그릴 유효한 데이터가 없습니다.")

x = df[x_col].to_numpy(dtype=float)
weight = df[weight_col].to_numpy(dtype=float)
derivative = df[derivative_col].to_numpy(dtype=float)

x_min, x_max = float(np.min(x)), float(np.max(x))
weight_min, weight_max = float(np.min(weight)), float(np.max(weight))
derivative_min, derivative_max = float(np.min(derivative)), float(np.max(derivative))

weight_pad = max((weight_max - weight_min) * 0.06, 1.0)
derivative_pad = max((derivative_max - derivative_min) * 0.08, 0.01)

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "color": "#222222",
    },
    "title": {
        "text": "열중량 분석 (TGA)",
        "left": "center",
        "top": 14,
        "textStyle": {"fontSize": 20, "fontWeight": "bold"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {"top": 48, "data": ["무게(%)", "미분무게(%/°C)"]},
    "grid": {"left": 78, "right": 78, "top": 94, "bottom": 76},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": x_min,
        "max": x_max,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisLabel": {"fontSize": 12},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "무게 (%)",
            "nameLocation": "middle",
            "nameGap": 54,
            "min": max(0, weight_min - weight_pad),
            "max": weight_max + weight_pad,
            "axisLine": {"show": True, "lineStyle": {"color": "#2878b5"}},
            "axisLabel": {"color": "#2878b5", "fontSize": 12},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "미분무게 (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "min": derivative_min - derivative_pad,
            "max": derivative_max + derivative_pad,
            "axisLine": {"show": True, "lineStyle": {"color": "#d1495b"}},
            "axisLabel": {"color": "#d1495b", "fontSize": 12},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "무게(%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#2878b5"},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
        },
        {
            "name": "미분무게(%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 1.8, "color": "#d1495b"},
            "data": [[float(a), float(b)] for a, b in zip(x, derivative)],
        },
    ],
}

result = {
    "figures": [
        {
            "name": "tga_korean_excel",
            "option": option,
            "width": 900,
            "height": 600,
            "dpi": 300,
            "formats": ["png", "pdf"],
        }
    ]
}

json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
sys.stdout.write("\n")
