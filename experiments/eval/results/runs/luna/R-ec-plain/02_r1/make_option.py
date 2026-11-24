import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
SHEET_NAME = "1006R1-V normal"


def find_column(columns, candidates):
    normalized = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    for c in columns:
        name = str(c).strip().lower()
        if any(candidate.lower() in name for candidate in candidates):
            return c
    raise ValueError(f"Could not find any of these columns: {candidates}")


df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
x_col = find_column(df.columns, ["Temperature"])
weight_col = find_column(df.columns, ["Weight(%)", "Weight"])
deriv_col = find_column(df.columns, ["D.W(%/C)", "Deriv.Weight", "D.W"])

for col in (x_col, weight_col, deriv_col):
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df[[x_col, weight_col, deriv_col]].dropna().sort_values(x_col)
if df.empty:
    raise ValueError("No numeric TGA rows found.")

temperature = df[x_col].to_numpy(dtype=float)
weight = df[weight_col].to_numpy(dtype=float)
deriv = df[deriv_col].to_numpy(dtype=float)

max_idx = int(np.nanargmax(deriv))
max_temperature = float(temperature[max_idx])
max_deriv = float(deriv[max_idx])

residue_idx = int(np.nanargmin(np.abs(temperature - 800.0)))
residue_temperature = float(temperature[residue_idx])
residue_weight = float(weight[residue_idx])

# Keep chart data compact while retaining the observed curve shape.
def downsample_indices(x, y, limit=1800):
    n = len(x)
    if n <= limit:
        return np.arange(n)
    bins = np.linspace(0, n, limit // 2 + 1, dtype=int)
    chosen = set()
    for left, right in zip(bins[:-1], bins[1:]):
        if right <= left:
            continue
        section = y[left:right]
        chosen.add(left + int(np.nanargmin(section)))
        chosen.add(left + int(np.nanargmax(section)))
    chosen.add(0)
    chosen.add(n - 1)
    return np.array(sorted(chosen), dtype=int)


indices = downsample_indices(temperature, weight)
weight_data = [[round(float(temperature[i]), 4), round(float(weight[i]), 5)] for i in indices]
indices_deriv = downsample_indices(temperature, deriv)
deriv_data = [[round(float(temperature[i]), 4), round(float(deriv[i]), 6)] for i in indices_deriv]

# Include the exact observed maximum in the displayed data.
if not any(abs(p[0] - max_temperature) < 1e-9 for p in deriv_data):
    deriv_data.append([round(max_temperature, 4), round(max_deriv, 6)])
    deriv_data.sort(key=lambda p: p[0])

y2_min = float(np.nanmin(deriv))
y2_max = float(np.nanmax(deriv))
y2_step = 0.2
y2_axis_min = np.floor(y2_min / y2_step) * y2_step
y2_axis_max = np.ceil(y2_max / y2_step) * y2_step
if y2_axis_max <= y2_axis_min:
    y2_axis_max = y2_axis_min + y2_step

option = {
    "backgroundColor": "#ffffff",
    "animation": False,
    "title": {
        "text": "1006R1-V normal TGA",
        "left": "center",
        "top": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 17, "fontWeight": "bold"},
    },
    "legend": {
        "top": 40,
        "data": ["Weight(%)", "Deriv.Weight"],
        "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 12},
    },
    "grid": {"left": 76, "right": 78, "top": 86, "bottom": 72},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 0,
        "max": 900,
        "interval": 200,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 11},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 12},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 100,
            "interval": 20,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 11},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 12},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "Deriv.Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "min": round(float(y2_axis_min), 6),
            "max": round(float(y2_axis_max), 6),
            "interval": y2_step,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 11},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 12},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 0,
            "data": weight_data,
            "lineStyle": {"width": 2, "color": "#2369a8"},
            "itemStyle": {"color": "#2369a8"},
            "markPoint": {
                "symbol": "pin",
                "symbolSize": 46,
                "data": [
                    {
                        "name": f"Residue {residue_weight:.2f}%",
                        "coord": [round(residue_temperature, 4), round(residue_weight, 5)],
                        "value": f"Residue {residue_weight:.2f}%",
                        "itemStyle": {"color": "#238b57"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_weight:.2f}%",
                            "fontFamily": "Noto Sans CJK KR, sans-serif",
                            "fontSize": 11,
                            "color": "#ffffff",
                        },
                    }
                ],
            },
        },
        {
            "name": "Deriv.Weight",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 1,
            "data": deriv_data,
            "lineStyle": {"width": 2, "color": "#d94b3d"},
            "itemStyle": {"color": "#d94b3d"},
            "markPoint": {
                "symbol": "pin",
                "symbolSize": 48,
                "data": [
                    {
                        "name": f"Max {max_deriv:.4f}",
                        "coord": [round(max_temperature, 4), round(max_deriv, 6)],
                        "value": f"Max {max_deriv:.4f}",
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": f"Max {max_deriv:.4f}",
                            "fontFamily": "Noto Sans CJK KR, sans-serif",
                            "fontSize": 11,
                            "color": "#ffffff",
                        },
                    }
                ],
            },
        },
    ],
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "1006R1-V_normal_TGA",
                    "option": option,
                    "width": 900,
                    "height": 600,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
