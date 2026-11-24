import json
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V acid")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight(%)"], errors="coerce").to_numpy()
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(derivative)
temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]

order = np.argsort(temperature)
temperature, weight, derivative = temperature[order], weight[order], derivative[order]

in_range = (temperature >= 100) & (temperature <= 800)
x, y_weight, y_derivative = temperature[in_range], weight[in_range], derivative[in_range]

# TGA derivative peaks are mass-loss events; select the two strongest negative peaks.
peak_indices, _ = find_peaks(-y_derivative, distance=max(1, len(y_derivative) // 30))
if len(peak_indices) < 2:
    peak_indices = np.argsort(y_derivative)[:min(2, len(y_derivative))]
else:
    peak_indices = peak_indices[np.argsort(y_derivative[peak_indices])[:2]]
peak_indices = sorted(peak_indices, key=lambda i: x[i])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": None
    },
    "legend": {
        "top": 10,
        "data": ["Weight(%)", "D.W(%/C)"]
    },
    "grid": {"left": 74, "right": 74, "top": 58, "bottom": 66},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 100,
        "max": 800,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisLabel": {"color": "#333333"},
        "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#3569a8"}},
            "axisLabel": {"color": "#3569a8"},
            "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}}
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLine": {"show": True, "lineStyle": {"color": "#d05a45"}},
            "axisLabel": {"color": "#d05a45"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": "#3569a8"},
            "data": [[float(a), float(b)] for a, b in zip(x, y_weight)]
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": "#d05a45"},
            "data": [[float(a), float(b)] for a, b in zip(x, y_derivative)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "itemStyle": {"color": "#f2a541", "borderColor": "#ffffff", "borderWidth": 2},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{b}",
                    "color": "#333333",
                    "fontSize": 11
                },
                "data": [
                    {
                        "name": f"Peak {i + 1}",
                        "coord": [float(x[idx]), float(y_derivative[idx])]
                    }
                    for i, idx in enumerate(peak_indices)
                ]
            }
        }
    ]
}

# Remove the optional formatter key: ECharts options must remain plain JSON.
option["tooltip"].pop("valueFormatter", None)

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_acid_TGA",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
