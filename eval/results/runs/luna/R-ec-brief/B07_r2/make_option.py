import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name=1)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
order = np.argsort(temperature)
temperature, weight, dtg = temperature[order], weight[order], dtg[order]

weight_at = {}
for target in (300, 600):
    idx = int(np.argmin(np.abs(temperature - target)))
    weight_at[target] = {
        "temperature": float(temperature[idx]),
        "weight": float(weight[idx]),
    }

def pairs(x, y):
    return [[float(a), float(b)] for a, b in zip(x, y)]

annotations = []
for target in (300, 600):
    point = weight_at[target]
    annotations.append({
        "name": f'{target} °C: {point["weight"]:.1f}%',
        "coord": [point["temperature"], point["weight"]],
        "value": "",
        "symbol": "circle",
        "symbolSize": 9,
        "itemStyle": {"color": "#1f4e9c", "borderColor": "#ffffff", "borderWidth": 1},
        "label": {
            "show": True,
            "formatter": f'{target} °C: {point["weight"]:.1f}%',
            "position": "top",
            "color": "#1f4e9c",
            "fontSize": 12,
            "backgroundColor": "rgba(255,255,255,0.85)",
            "padding": [3, 5],
        },
    })

peak_mask = temperature > 150
peak_idx = np.flatnonzero(peak_mask)[np.argmax(-dtg[peak_mask])]

option = {
    "animation": False,
    "title": {
        "text": "PVC",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight (%)", "-DTG"], "left": "center", "bottom": 8},
    "grid": {"left": 70, "right": 70, "top": 55, "bottom": 75},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 35,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": pairs(temperature, weight),
            "showSymbol": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {"data": annotations},
        },
        {
            "name": "-DTG",
            "type": "line",
            "yAxisIndex": 1,
            "data": pairs(temperature, -dtg),
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 1.6},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {
                "data": [{
                    "coord": [float(temperature[peak_idx]), float(-dtg[peak_idx])],
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": f'{temperature[peak_idx]:.0f} °C',
                        "position": "top",
                        "color": "#c0392b",
                        "fontSize": 12,
                    },
                }]
            },
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "PVC",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
