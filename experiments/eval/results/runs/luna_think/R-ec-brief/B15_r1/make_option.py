import json
import re
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

book = pd.ExcelFile(DATA_FILE)
colors = ["#1f4e9c", "#c0392b", "#2e8b57"]
series = []
legend_names = []
all_temperatures = []

for index, sheet in enumerate(book.sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    if df.shape[1] < 4:
        continue

    temp = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")
    derivative = pd.to_numeric(df.iloc[:, 3], errors="coerce")
    valid = temp.notna() & weight.notna() & derivative.notna()
    temp = temp[valid].to_numpy(dtype=float)
    weight = weight[valid].to_numpy(dtype=float)
    derivative = derivative[valid].to_numpy(dtype=float)
    if len(temp) == 0:
        continue

    order = np.argsort(temp)
    temp, weight, derivative = temp[order], weight[order], derivative[order]
    all_temperatures.extend(temp.tolist())
    color = colors[index % len(colors)]
    legend_names.append(str(sheet))

    residue_idx = int(np.argmin(np.abs(temp - 800.0)))
    weight_data = [[float(x), float(y)] for x, y in zip(temp, weight)]
    weight_series = {
        "name": str(sheet),
        "type": "line",
        "xAxisIndex": 0,
        "yAxisIndex": 0,
        "data": weight_data,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"color": color, "width": 2},
        "itemStyle": {"color": color},
        "markPoint": {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": f"Residue {weight[residue_idx]:.1f}%",
                "position": "top",
                "color": color,
                "fontSize": 11,
                "backgroundColor": "rgba(255,255,255,0.85)",
                "padding": [2, 4],
            },
            "data": [{
                "name": "Residue",
                "coord": [float(temp[residue_idx]), float(weight[residue_idx])],
            }],
        },
    }
    series.append(weight_series)

    candidates = np.where(temp > 150.0)[0]
    if len(candidates):
        peak_idx = int(candidates[np.argmax(-derivative[candidates])])
        peak_value = float(-derivative[peak_idx])
        dtg_series = {
            "name": f"{sheet} DTG",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[float(x), float(-y)] for x, y in zip(temp, derivative)],
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": color, "width": 1.7, "type": "dashed"},
            "itemStyle": {"color": color},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"{temp[peak_idx]:.0f} °C",
                    "position": "top",
                    "color": color,
                    "fontSize": 11,
                    "backgroundColor": "rgba(255,255,255,0.85)",
                    "padding": [2, 4],
                },
                "data": [{
                    "name": "DTG peak",
                    "coord": [float(temp[peak_idx]), peak_value],
                }],
            },
        }
        series.append(dtg_series)

xmin = float(min(all_temperatures)) if all_temperatures else 0
xmax = float(max(all_temperatures)) if all_temperatures else 900

option = {
    "animation": False,
    "title": {"text": "TGA", "left": "center", "top": 10},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {
        "data": legend_names,
        "orient": "vertical",
        "right": 10,
        "top": "middle",
        "selectedMode": True,
    },
    "grid": {"left": 75, "right": 155, "top": 65, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": xmin,
        "max": xmax,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "−DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"show": True},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "polymers_overlay",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
