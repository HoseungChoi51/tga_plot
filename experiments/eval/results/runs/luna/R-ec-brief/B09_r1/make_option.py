import json
import math
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PE")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

residue_index = int(abs(temperature - 800).argmin())
residue_x = float(temperature[residue_index])
residue_y = float(weight[residue_index])

peak_candidates = (temperature > 150) & (dtg < 0)
if peak_candidates.any():
    candidate_indices = [i for i, ok in enumerate(peak_candidates) if ok]
    peak_index = max(candidate_indices, key=lambda i: -dtg[i])
    peak_x = float(temperature[peak_index])
    peak_y = float(-dtg[peak_index])
else:
    peak_x = None
    peak_y = None

weight_data = [
    [float(x), float(y)] for x, y in zip(temperature, weight)
    if math.isfinite(float(x)) and math.isfinite(float(y))
]
dtg_data = [
    [float(x), float(-y)] for x, y in zip(temperature, dtg)
    if math.isfinite(float(x)) and math.isfinite(float(y))
]

weight_marks = [
    {
        "coord": [residue_x, residue_y],
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_y:.1f}%",
            "position": "right",
            "color": "#333333",
            "fontFamily": "Noto Sans CJK KR",
        },
    }
]
dtg_marks = []
if peak_x is not None:
    dtg_marks.append({
        "coord": [peak_x, peak_y],
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#c0392b"},
        "label": {
            "show": True,
            "formatter": f"{peak_x:.0f} °C",
            "position": "top",
            "color": "#333333",
            "fontFamily": "Noto Sans CJK KR",
        },
    })

option = {
    "animation": False,
    "title": {
        "text": "PE",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"left": "center", "top": "middle", "orient": "vertical"},
    "grid": {"left": 72, "right": 72, "top": 64, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 100,
        "max": 700,
        "interval": 100,
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
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": weight_data,
            "showSymbol": False,
            "lineStyle": {"color": "#ff0000", "width": 3},
            "itemStyle": {"color": "#ff0000"},
            "markPoint": {"data": weight_marks},
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 1.5},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {"data": dtg_marks},
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "PE",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
