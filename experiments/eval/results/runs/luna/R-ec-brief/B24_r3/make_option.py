import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PE")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy(dtype=float) + 273.15
weight = weight[valid].to_numpy(dtype=float)
dtg = dtg[valid].to_numpy(dtype=float)

residue_idx = int(np.argmin(np.abs(temperature - (800 + 273.15))))
peak_candidates = np.where(temperature > 150 + 273.15)[0]
peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])]) if len(peak_candidates) else int(np.argmax(-dtg))

x_min = float(np.min(temperature))
x_max = float(np.max(temperature))
weight_max = float(np.max(weight))
dtg_plot = -dtg
dtg_max = float(np.max(dtg_plot))

option = {
    "title": {
        "text": "PE",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "animation": False,
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight (%)", "-DTG (%/°C)"],
        "left": "left",
        "top": "middle",
        "orient": "vertical"
    },
    "grid": {"left": 82, "right": 82, "top": 65, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (K)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": x_min,
        "max": x_max,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 55,
            "min": 0,
            "max": max(105, weight_max * 1.05),
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 55,
            "min": 0,
            "max": dtg_max * 1.12 if dtg_max > 0 else 1,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {weight[residue_idx]:.1f}%",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "data": [{
                    "coord": [float(temperature[residue_idx]), float(weight[residue_idx])]
                }]
            }
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "data": [[float(x), float(y)] for x, y in zip(temperature, dtg_plot)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{temperature[peak_idx]:.0f} K",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "data": [{
                    "coord": [float(temperature[peak_idx]), float(dtg_plot[peak_idx])]
                }]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "PE",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
