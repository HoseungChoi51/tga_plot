import json
import os
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
cols = {str(c).strip().lower(): c for c in df.columns}

def find_col(words):
    for key, col in cols.items():
        if any(word in key for word in words):
            return col
    return None

xcol = find_col(["temperature", "temp"])
wcol = find_col(["weight"])
dcol = find_col(["deriv", "dtg"])

if xcol is None or wcol is None or dcol is None:
    raise ValueError("Could not identify temperature, weight, and derivative-weight columns.")

x = pd.to_numeric(df[xcol], errors="coerce").to_numpy()
weight = pd.to_numeric(df[wcol], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dcol], errors="coerce").to_numpy()

valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
x, weight, dtg = x[valid], weight[valid], dtg[valid]
order = np.argsort(x)
x, weight, dtg = x[order], weight[order], dtg[order]

weight_data = [[float(a), float(b)] for a, b in zip(x, weight)]
dtg_data = [[float(a), float(-b)] for a, b in zip(x, dtg)]

bands = [
    (120, 250, "H₂O", "rgba(52, 152, 219, 0.16)"),
    (430, 580, "CO", "rgba(46, 204, 113, 0.16)"),
    (640, 830, "CO₂", "rgba(243, 156, 18, 0.17)"),
]

mark_areas = [
    [
        {"name": label, "xAxis": start, "itemStyle": {"color": color}},
        {"xAxis": end},
    ]
    for start, end, label, color in bands
]

mark_points = []
residue_idx = int(np.argmin(np.abs(x - 800)))
mark_points.append({
    "name": f"Residue {weight[residue_idx]:.1f}%",
    "coord": [float(x[residue_idx]), float(weight[residue_idx])],
    "value": f"Residue {weight[residue_idx]:.1f}%",
    "symbol": "circle",
    "symbolSize": 8,
    "itemStyle": {"color": "#1f4e9c"},
    "label": {"show": True, "position": "top", "formatter": f"Residue {weight[residue_idx]:.1f}%"},
})

peak_mask = x > 150
if np.any(peak_mask):
    eligible = np.where(peak_mask)[0]
    peak_idx = int(eligible[np.argmax(-dtg[eligible])])
    mark_points.append({
        "name": f"{x[peak_idx]:.0f} °C",
        "coord": [float(x[peak_idx]), float(-dtg[peak_idx])],
        "value": f"{x[peak_idx]:.0f} °C",
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#c0392b"},
        "label": {"show": True, "position": "top", "formatter": f"{x[peak_idx]:.0f} °C"},
    })

option = {
    "animation": False,
    "title": {
        "text": os.path.splitext(os.path.basename(DATA_FILE))[0],
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight (%)", "-DTG (%/°C)"], "left": "center", "top": 34},
    "grid": {"left": 72, "right": 72, "top": 86, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 950,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisTick": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisTick": {"show": True},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "showSymbol": False,
            "data": weight_data,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "markPoint": {"data": mark_points},
            "markArea": {
                "silent": True,
                "label": {
                    "show": True,
                    "position": "insideTop",
                    "color": "#333333",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 13,
                },
                "data": mark_areas,
            },
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": dtg_data,
            "lineStyle": {"width": 1.8, "color": "#c0392b"},
        },
    ],
}

result = {
    "figures": [{
        "name": "caox",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
