import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)
dtg = dtg[valid].to_numpy(dtype=float)

# Residue: measured weight nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = float(temperature[residue_idx])
residue_weight = float(weight[residue_idx])

# DTG is negative during mass loss; invert so peaks point upward.
dtg_inverted = -dtg
peak_candidates = np.flatnonzero(temperature > 150)
peak_idx = int(peak_candidates[np.argmax(dtg_inverted[peak_candidates])])
peak_temp = float(temperature[peak_idx])
peak_value = float(dtg_inverted[peak_idx])

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#333333"},
    "title": {
        "text": "Raw",
        "left": "center",
        "textStyle": {"fontSize": 16, "fontWeight": "normal"}
    },
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {"data": ["Weight (%)", "-DTG (%/°C)"], "left": "center", "bottom": 8},
    "grid": {"left": 72, "right": 72, "top": 58, "bottom": 72},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "inverse": True,
        "min": float(np.nanmin(temperature)),
        "max": float(np.nanmax(temperature)),
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"color": "#1f4e9c"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "inverse": False,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"color": "#c0392b"},
            "splitLine": {"show": False}
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
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "right",
                    "color": "#1f4e9c",
                    "fontSize": 12
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(x), float(y)] for x, y in zip(temperature, dtg_inverted)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{peak_temp:.0f} °C",
                    "position": "top",
                    "color": "#c0392b",
                    "fontSize": 12
                },
                "data": [{"coord": [peak_temp, peak_value]}]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "Raw",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
