import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V acid"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_col(key):
    for col in df.columns:
        if key.lower() in col.lower():
            return col
    raise KeyError(f"Could not find column matching {key!r}")

x_col = find_col("Temperature")
weight_col = find_col("Weight")
dtg_col = find_col("D.W")

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(x_col)

x = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg_up = -data[dtg_col].to_numpy(dtype=float)

# Find the two largest DTG peaks above 150 °C, requiring local maxima.
mask = x > 150
indices = np.flatnonzero(mask)
candidates = [
    i for i in indices
    if (i == 0 or dtg_up[i] >= dtg_up[i - 1])
    and (i == len(x) - 1 or dtg_up[i] >= dtg_up[i + 1])
]
if not candidates:
    candidates = list(indices)

peak_indices = sorted(candidates, key=lambda i: dtg_up[i], reverse=True)[:2]
peak_indices.sort(key=lambda i: x[i])

peak_markers = [
    {
        "coord": [float(x[i]), float(dtg_up[i])],
        "symbol": "circle",
        "symbolSize": 9,
        "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1},
        "label": {
            "show": True,
            "formatter": f"{x[i]:.0f} °C",
            "position": "top",
            "color": "#c0392b",
            "fontSize": 12,
            "fontFamily": "Noto Sans CJK KR",
        },
    }
    for i in peak_indices
]

option = {
    "animation": False,
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight (%)", "-DTG (%/°C)"],
        "left": 12,
        "top": "middle",
        "orient": "vertical",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
    },
    "grid": {"left": 95, "right": 85, "top": 65, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
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
            "nameGap": 55,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 55,
            "position": "right",
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, dtg_up)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {"data": peak_markers},
        },
    ],
}

print(json.dumps(
    {
        "figures": [
            {
                "name": "1006R1-V_acid",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        ]
    },
    ensure_ascii=False,
    allow_nan=False,
))
