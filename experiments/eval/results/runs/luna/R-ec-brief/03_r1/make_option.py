import json
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET = "1006R1-V acid"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET)
df.columns = [str(c).strip() for c in df.columns]

def find_column(*terms):
    for col in df.columns:
        name = col.lower().replace(" ", "")
        if all(term.lower().replace(" ", "") in name for term in terms):
            return col
    raise ValueError(f"Could not identify column matching {terms}")

x_col = find_column("temperature")
weight_col = find_column("weight")
dtg_col = next(
    (col for col in df.columns if "d.w" in col.lower() or "dtg" in col.lower()),
    None,
)
if dtg_col is None:
    raise ValueError("Could not identify the DTG column")

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(x_col)
x = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

# DTG loss peaks point upward after sign inversion; report the two strongest
# distinct local peaks above 150 °C.
peak_indices, _ = find_peaks(-dtg, distance=3)
peak_indices = [i for i in peak_indices if x[i] > 150]
if not peak_indices:
    peak_indices = [i for i in range(len(x)) if x[i] > 150]
peak_indices = sorted(peak_indices, key=lambda i: -dtg[i])[:2]
peak_indices = sorted(peak_indices, key=lambda i: x[i])

series = [
    {
        "name": "Weight",
        "type": "line",
        "showSymbol": False,
        "yAxisIndex": 0,
        "lineStyle": {"color": "#1f4e9c", "width": 2},
        "data": [[float(a), float(b)] for a, b in zip(x, weight)],
    },
    {
        "name": "DTG",
        "type": "line",
        "showSymbol": False,
        "yAxisIndex": 1,
        "lineStyle": {"color": "#c0392b", "width": 1.8},
        "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
    },
]

for i, idx in enumerate(peak_indices, start=1):
    series.append({
        "name": f"DTG peak {i}",
        "type": "scatter",
        "yAxisIndex": 1,
        "symbolSize": 9,
        "itemStyle": {"color": "#c0392b"},
        "data": [{
            "value": [float(x[idx]), float(-dtg[idx])],
            "label": {
                "show": True,
                "formatter": f"{x[idx]:.0f} °C",
                "position": "top",
                "color": "#333333",
                "fontSize": 12,
            },
        }],
    })

option = {
    "title": {
        "text": SHEET,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight", "DTG"], "left": "center left", "top": "middle"},
    "grid": {"left": 80, "right": 80, "top": 65, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 100,
        "max": 800,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_acid",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
