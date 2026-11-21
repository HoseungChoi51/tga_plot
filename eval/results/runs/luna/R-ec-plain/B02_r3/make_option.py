import json
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

def find_column(fragment):
    for col in df.columns:
        if fragment.lower() in col.lower():
            return col
    raise ValueError(f"Column containing {fragment!r} not found")

xcol = find_column("Temperature")
wcol = find_column("Weight")
hcol = find_column("Heat Flow")

data = df[[xcol, wcol, hcol]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(xcol).drop_duplicates(subset=xcol)
x = data[xcol].to_numpy(dtype=float)
weight = data[wcol].to_numpy(dtype=float)
heat = data[hcol].to_numpy(dtype=float)

# Use prominent extrema in heat flow. In this dataset, upward excursions are
# treated as endothermic and downward excursions as exothermic.
prominence = max(float(np.ptp(heat)) * 0.025, 1e-12)
peaks_up, props_up = find_peaks(heat, prominence=prominence, distance=max(1, len(heat) // 40))
peaks_down, props_down = find_peaks(-heat, prominence=prominence, distance=max(1, len(heat) // 40))

# Keep the two strongest upward peaks and the strongest downward peak.
endo_indices = sorted(peaks_up, key=lambda i: heat[i], reverse=True)[:2]
exo_indices = sorted(peaks_down, key=lambda i: heat[i])[:1]

# Ensure labels are assigned consistently in ascending temperature order.
endo_indices = sorted(endo_indices, key=lambda i: x[i])

heat_min, heat_max = float(np.min(heat)), float(np.max(heat))
heat_pad = max((heat_max - heat_min) * 0.12, 0.05)

series = [
    {
        "name": "Weight",
        "type": "line",
        "yAxisIndex": 0,
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": "#2878B5"},
        "data": [[round(float(a), 5), round(float(b), 5)] for a, b in zip(x, weight)],
    },
    {
        "name": "Heat Flow",
        "type": "line",
        "yAxisIndex": 1,
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": "#D9534F"},
        "data": [[round(float(a), 5), round(float(b), 6)] for a, b in zip(x, heat)],
        "markPoint": {
            "symbol": "circle",
            "symbolSize": 10,
            "label": {
                "show": True,
                "color": "#222",
                "fontSize": 11,
                "formatter": "{b}\n{c|{c}}",
            },
            "data": [],
        },
    },
]

markpoints = []
for n, i in enumerate(endo_indices, 1):
    markpoints.append({
        "name": f"흡열 피크 {n}",
        "coord": [round(float(x[i]), 4), round(float(heat[i]), 6)],
        "value": f"{x[i]:.1f} °C",
        "itemStyle": {"color": "#D9534F"},
        "label": {
            "show": True,
            "position": "top",
            "formatter": f"흡열 {n}\n{x[i]:.1f} °C",
            "color": "#B33A36",
            "fontSize": 11,
        },
    })
for i in exo_indices:
    markpoints.append({
        "name": "발열 피크",
        "coord": [round(float(x[i]), 4), round(float(heat[i]), 6)],
        "value": f"{x[i]:.1f} °C",
        "itemStyle": {"color": "#2878B5"},
        "label": {
            "show": True,
            "position": "bottom",
            "formatter": f"발열\n{x[i]:.1f} °C",
            "color": "#21618C",
            "fontSize": 11,
        },
    })
series[1]["markPoint"]["data"] = markpoints

option = {
    "animation": False,
    "title": {
        "text": "TGA 및 Heat Flow",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {"data": ["Weight", "Heat Flow"], "top": 30},
    "grid": {"left": 78, "right": 82, "top": 78, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "axisLine": {"lineStyle": {"color": "#555"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": max(0, float(np.floor(np.min(weight) / 5) * 5)),
            "max": float(np.ceil(np.max(weight) / 5) * 5),
            "axisLine": {"show": True, "lineStyle": {"color": "#2878B5"}},
            "axisLabel": {"color": "#2878B5"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "Heat Flow (W/g)",
            "nameLocation": "middle",
            "nameGap": 56,
            "min": heat_min - heat_pad,
            "max": heat_max + heat_pad,
            "axisLine": {"show": True, "lineStyle": {"color": "#D9534F"}},
            "axisLabel": {"color": "#D9534F"},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

figure = {
    "name": "caox_tga_heatflow",
    "option": option,
    "width": 900,
    "height": 600,
    "dpi": 300,
    "formats": ["png"],
}
print(json.dumps({"figures": [figure]}, ensure_ascii=False, allow_nan=False))
