import json
import math
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def clean_number(value):
    if pd.isna(value):
        return None
    value = float(value)
    return value if math.isfinite(value) else None

# Load only the requested worksheet.
df = pd.read_excel(DATA_FILE, sheet_name="PVC")
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    for col in df.columns:
        if re.search(pattern, col, flags=re.IGNORECASE):
            return col
    raise ValueError(f"Required column not found: {pattern}")

x_col = find_column(r"temperature")
weight_col = find_column(r"weight\s*\(")
dtg_col = find_column(r"deriv")

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
x = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

# Residue at the measured temperature nearest 800 °C.
residue_index = int(np.argmin(np.abs(x - 800.0)))
residue_x = float(x[residue_index])
residue_y = float(weight[residue_index])

# Highest positive mass-loss peak (DTG is negative during mass loss), above 150 °C.
eligible = np.flatnonzero(x > 150.0)
peak_index = int(eligible[np.argmin(dtg[eligible])])
peak_x = float(x[peak_index])
peak_y = float(-dtg[peak_index])

weight_data = [[clean_number(a), clean_number(b)] for a, b in zip(x, weight)]
dtg_data = [[clean_number(a), clean_number(-b)] for a, b in zip(x, dtg)]

option = {
    "animation": False,
    "title": {
        "text": "PVC",
        "left": "center",
        "top": 12,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 24, "fontWeight": "bold"},
    },
    "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {
        "data": ["Weight (%)", "DTG (-Deriv. Weight)"],
        "left": "center",
        "top": 48,
        "textStyle": {"fontSize": 16},
    },
    "grid": {"left": 90, "right": 90, "top": 100, "bottom": 72, "containLabel": True},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontSize": 16},
        "nameTextStyle": {"fontSize": 16},
        "axisLine": {"lineStyle": {"color": "#555"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 54,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 56,
            "min": 0,
            "max": 1.2,
            "axisLabel": {"fontSize": 16},
            "nameTextStyle": {"fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": weight_data,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"color": "#1f4e9c", "width": 3},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "data": [
                    {
                        "name": "Residue",
                        "coord": [residue_x, residue_y],
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_y:.1f}%",
                            "position": "top",
                            "fontSize": 16,
                            "color": "#1f4e9c",
                            "backgroundColor": "rgba(255,255,255,0.85)",
                            "padding": [4, 6],
                        },
                    }
                ],
            },
        },
        {
            "name": "DTG (-Deriv. Weight)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"color": "#c0392b", "width": 3},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "data": [
                    {
                        "name": "DTG peak",
                        "coord": [peak_x, peak_y],
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": f"{peak_x:.0f} °C",
                            "position": "top",
                            "fontSize": 16,
                            "color": "#c0392b",
                            "backgroundColor": "rgba(255,255,255,0.85)",
                            "padding": [4, 6],
                        },
                    }
                ],
            },
        },
    ],
}

result = {
    "figures": [
        {
            "name": "PVC",
            "option": option,
            "width": 960,
            "height": 576,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
