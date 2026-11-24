import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg_for_weight = dtg[valid].to_numpy()

dtg_valid = np.isfinite(dtg_for_weight)
x_dtg = temperature[dtg_valid]
y_dtg = -dtg_for_weight[dtg_valid]

residue_index = int(np.argmin(np.abs(temperature - 800)))
residue_x = float(temperature[residue_index])
residue_y = float(weight[residue_index])

peak_candidates = np.isfinite(y_dtg) & (x_dtg > 150)
if peak_candidates.any():
    peak_local_index = int(np.argmax(y_dtg[peak_candidates]))
    peak_x = float(x_dtg[peak_candidates][peak_local_index])
    peak_y = float(y_dtg[peak_candidates][peak_local_index])
else:
    peak_x = None
    peak_y = None

option = {
    "title": {
        "text": "Raw",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "legend": {
        "data": ["Weight (%)", "-Deriv. Weight (%/°C)", f"Residue {residue_y:.1f}%"],
        "left": "center",
        "top": "8%"
    },
    "grid": {"left": 72, "right": 72, "top": 68, "bottom": 62},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "inverse": True,
        "min": float(np.nanmin(temperature)),
        "max": float(np.nanmax(temperature)),
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "-Deriv. Weight (%/°C)",
            "position": "right",
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
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "data": [
                    {
                        "name": f"Residue {residue_y:.1f}%",
                        "coord": [residue_x, residue_y],
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_y:.1f}%",
                            "position": "right"
                        }
                    }
                ]
            }
        },
        {
            "name": "-Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(x), float(y)] for x, y in zip(x_dtg, y_dtg)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "data": (
                    [{
                        "name": f"{peak_x:.0f} °C",
                        "coord": [peak_x, peak_y],
                        "label": {
                            "show": True,
                            "formatter": f"{peak_x:.0f} °C",
                            "position": "top"
                        }
                    }]
                    if peak_x is not None else []
                )
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "raw",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
