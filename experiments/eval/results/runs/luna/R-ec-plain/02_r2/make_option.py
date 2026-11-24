import json
import math
import re
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

def clean_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None

try:
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
except Exception as exc:
    print(json.dumps({"figures": [], "error": str(exc)}, ensure_ascii=False))
    sys.exit(0)

# Select the requested B, C, and D columns (Temperature, Weight, Deriv.Weight).
temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy(dtype=float)
weight = pd.to_numeric(df.iloc[:, 2], errors="coerce").to_numpy(dtype=float)
derivative = pd.to_numeric(df.iloc[:, 3], errors="coerce").to_numpy(dtype=float)

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(derivative)
temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]

if len(temperature) == 0:
    print(json.dumps({"figures": []}, ensure_ascii=False))
    sys.exit(0)

order = np.argsort(temperature)
temperature, weight, derivative = temperature[order], weight[order], derivative[order]

# Residue is the weight at the measured temperature closest to 800 C.
residue_index = int(np.argmin(np.abs(temperature - 800.0)))
residue_temp = float(temperature[residue_index])
residue_weight = float(weight[residue_index])

# Report the most negative derivative value, corresponding to the maximum
# magnitude of weight-loss rate, as the Deriv.Weight peak.
peak_index = int(np.argmin(derivative))
peak_temp = float(temperature[peak_index])
peak_value = float(derivative[peak_index])

x_min = 0
x_max = int(math.ceil(float(np.max(temperature)) / 200.0) * 200)
if x_max == 0:
    x_max = 200

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "color": "#273449"
    },
    "title": {
        "text": "1006R1-V normal TGA",
        "left": "center",
        "top": 14,
        "textStyle": {"fontSize": 18, "fontWeight": "bold"}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": "{value}"
    },
    "legend": {
        "top": 44,
        "data": ["Weight (%)", "Deriv.Weight (%/°C)"]
    },
    "grid": {"left": 82, "right": 88, "top": 92, "bottom": 72},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": x_min,
        "max": x_max,
        "interval": 200,
        "axisLabel": {"formatter": "{value}"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5eaf0"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 54,
            "min": 0,
            "max": 100,
            "interval": 20,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5eaf0"}}
        },
        {
            "type": "value",
            "name": "Deriv.Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "position": "right",
            "min": -1.2,
            "max": 0.2,
            "interval": 0.2,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2.2, "color": "#2369a8"},
            "data": [
                [clean_number(x), clean_number(y)]
                for x, y in zip(temperature, weight)
            ],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "itemStyle": {"color": "#e4572e"},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": f"Residue {residue_weight:.2f}%\n({residue_temp:.1f}°C)",
                    "fontSize": 12,
                    "fontWeight": "bold"
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        },
        {
            "name": "Deriv.Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 1.8, "color": "#d1495b"},
            "data": [
                [clean_number(x), clean_number(y)]
                for x, y in zip(temperature, derivative)
            ],
            "markPoint": {
                "symbol": "diamond",
                "symbolSize": 12,
                "itemStyle": {"color": "#8c2f39"},
                "label": {
                    "show": True,
                    "position": "bottom",
                    "formatter": f"Deriv.Weight max: {peak_value:.4f}\n{peak_temp:.1f}°C",
                    "fontSize": 11,
                    "fontWeight": "bold"
                },
                "data": [{"coord": [peak_temp, peak_value]}]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_normal_TGA",
        "option": option,
        "width": 1000,
        "height": 650,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
