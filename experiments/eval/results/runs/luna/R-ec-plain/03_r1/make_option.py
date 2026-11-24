import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V acid")
df.columns = [str(c).strip() for c in df.columns]

x = pd.to_numeric(df["Temperature"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight(%)"], errors="coerce").to_numpy()
dw = pd.to_numeric(df["D.W(%/C)"], errors="coerce").to_numpy()

valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dw)
x, weight, dw = x[valid], weight[valid], dw[valid]

order = np.argsort(x)
x, weight, dw = x[order], weight[order], dw[order]

# DTG mass-loss peaks appear as minima in D.W(%/C).
in_range = (x >= 100) & (x <= 800)
peak_indices, _ = find_peaks(-dw[in_range], distance=15, prominence=0.01)
range_indices = np.flatnonzero(in_range)
peak_indices = range_indices[peak_indices]

# Retain the two strongest peaks and display them in temperature order.
peak_indices = sorted(peak_indices, key=lambda i: dw[i])[:2]
peak_indices.sort(key=lambda i: x[i])

def clean_number(value):
    value = float(value)
    return value if np.isfinite(value) else None

weight_data = [
    [clean_number(a), clean_number(b)]
    for a, b in zip(x, weight)
    if 100 <= a <= 800
]
dtg_data = [
    [clean_number(a), clean_number(b)]
    for a, b in zip(x, dw)
    if 100 <= a <= 800
]

peak_data = [
    {
        "name": f"Peak {n}",
        "coord": [clean_number(x[i]), clean_number(dw[i])],
        "value": [clean_number(x[i]), clean_number(dw[i])],
        "label": {
            "show": True,
            "formatter": f"Peak {n}\\n{{c}}",
            "position": "top",
            "distance": 8,
            "fontSize": 11,
            "color": "#333333",
        },
        "symbolSize": 11,
        "itemStyle": {"color": "#d62728", "borderColor": "#ffffff", "borderWidth": 1},
    }
    for n, i in enumerate(peak_indices, start=1)
]

option = {
    "animation": False,
    "title": {
        "text": "1006R1-V acid",
        "left": "center",
        "top": 8,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {"data": ["Weight(%)", "D.W(%/C)"], "top": 34},
    "grid": {"left": 78, "right": 78, "top": 78, "bottom": 66},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 36,
        "min": 100,
        "max": 800,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "inverse": True,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": weight_data,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#1f77b4"},
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#ff7f0e"},
            "markPoint": {"data": peak_data},
        },
    ],
}

result = {
    "figures": [
        {
            "name": "1006R1-V_acid",
            "option": option,
            "width": 800,
            "height": 520,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}
json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False)
