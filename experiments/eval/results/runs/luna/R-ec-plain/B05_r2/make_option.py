import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]


def read_data(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        # Text exports are commonly tab- or whitespace-delimited.
        try:
            df = pd.read_csv(path, sep=None, engine="python")
            if df.shape[1] < 3:
                df = pd.read_csv(path, sep=r"\s+", engine="python")
        except Exception:
            df = pd.read_csv(path, sep=r"\s+", engine="python")

    df.columns = [str(c).strip() for c in df.columns]
    temp_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)
    deriv_col = next(c for c in df.columns if "Deriv" in c)

    result = pd.DataFrame({
        "temperature": pd.to_numeric(df[temp_col], errors="coerce"),
        "weight": pd.to_numeric(df[weight_col], errors="coerce"),
        "deriv": pd.to_numeric(df[deriv_col], errors="coerce"),
    }).dropna()
    return result.sort_values("temperature")


series = []
colors = ["#2563EB", "#DC2626"]

for path, label, color in zip(DATA_FILES, ["Lot A", "Lot B"], colors):
    data = read_data(path)
    series.extend([
        {
            "name": label,
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": color},
            "itemStyle": {"color": color},
            "data": [
                [round(float(x), 6), round(float(y), 6)]
                for x, y in zip(data["temperature"], data["weight"])
            ],
        },
        {
            "name": f"{label} Derivative",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 1.5, "color": color, "type": "dashed"},
            "itemStyle": {"color": color},
            "data": [
                [round(float(x), 6), round(float(y), 6)]
                for x, y in zip(data["temperature"], data["deriv"])
            ],
        },
    ])

option = {
    "animation": False,
    "backgroundColor": "#FFFFFF",
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#222222"},
    "title": {
        "text": "TGA Comparison",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 16, "fontWeight": "normal"},
    },
    "legend": {
        "data": ["Lot A", "Lot B", "Lot A Derivative", "Lot B Derivative"],
        "top": 40,
        "left": "center",
        "itemGap": 18,
        "textStyle": {"fontSize": 11},
    },
    "grid": {"left": 76, "right": 78, "top": 82, "bottom": 62},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisTick": {"show": True},
        "splitLine": {"lineStyle": {"color": "#E5E7EB"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "splitLine": {"lineStyle": {"color": "#E5E7EB"}},
        },
        {
            "type": "value",
            "name": "Derivative (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": -1.3,
            "max": 0.1,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "tga_lot_comparison",
        "option": option,
        "width": 900,
        "height": 600,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
