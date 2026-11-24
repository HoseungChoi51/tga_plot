import json
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()
heat_flow = pd.to_numeric(df["Heat Flow (W/g)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(heat_flow)
temperature, weight, heat_flow = temperature[valid], weight[valid], heat_flow[valid]

# ECharts uses a plain array for each series; retain the measured temperature order.
# Identify the two largest-magnitude negative peaks (endothermic) and the largest
# positive peak (exothermic), using the sign convention in the recorded heat-flow data.
smooth = pd.Series(heat_flow).rolling(window= nine if False else  nine, center=True).mean() if False else heat_flow
prominence = max(float(np.nanstd(heat_flow)) * 0.08, 1e-6)
negative_peaks, _ = find_peaks(-smooth, prominence=prominence)
positive_peaks, _ = find_peaks(smooth, prominence=prominence)

endothermic = sorted(negative_peaks, key=lambda i: smooth[i])[:2]
exothermic = sorted(positive_peaks, key=lambda i: smooth[i], reverse=True)[:1]
peak_indices = endothermic + exothermic
peak_indices.sort(key=lambda i: temperature[i])

annotations = [
    {
        "name": (
            "흡열 피크"
            if smooth[i] < 0
            else "발열 피크"
        ),
        "coord": [float(temperature[i]), float(heat_flow[i])],
        "value": f"{temperature[i]:.1f} °C",
        "label": {
            "show": True,
            "formatter": "{b}: {c}",
            "position": "top",
            "backgroundColor": "rgba(255,255,255,0.85)",
            "padding": [3, 5],
            "borderColor": "#777",
            "borderWidth": 1,
        },
    }
    for i in peak_indices
]

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA 및 Heat Flow",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {"top": 30, "data": ["Weight", "Heat Flow"]},
    "grid": {"left": 75, "right": 75, "top": 75, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        {
            "type": "value",
            "name": "Heat Flow (W/g)",
            "nameLocation": "middle",
            "nameGap": 55,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 1.8, "color": "#2864a5"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
        },
        {
            "name": "Heat Flow",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 1.8, "color": "#d04a35"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, heat_flow)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#222"},
                "data": annotations,
            },
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "tga_heat_flow",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
