import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

colors = {"PE": "#1f4e9c", "PVC": "#c0392b", "PET": "#2e8b57"}
series = []
all_temperatures = []
all_weights = []
all_dtg = []

book = pd.ExcelFile(DATA_FILE)
for sheet in book.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    if not {"Temperature (°C)", "Weight (%)", "Deriv. Weight (%/°C)"}.issubset(df.columns):
        continue

    x = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce").to_numpy()
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if len(x) == 0:
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]
    color = colors.get(sheet, "#666666")

    # Keep each sheet's weight and inverted derivative curves identifiable in the legend.
    series.extend([
        {
            "name": f"{sheet} Weight",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": color},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
        },
        {
            "name": f"{sheet} DTG",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 1.7, "type": "dashed", "color": color},
            "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
        },
    ])
    all_temperatures.extend(x.tolist())
    all_weights.extend(weight.tolist())
    all_dtg.extend((-dtg).tolist())

x_min, x_max = min(all_temperatures), max(all_temperatures)
w_min, w_max = min(all_weights), max(all_weights)
d_min, d_max = min(all_dtg), max(all_dtg)
w_pad = max(3, (w_max - w_min) * 0.06)
d_pad = max(0.1, (d_max - d_min) * 0.08)

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "title": {
        "text": "PE, PVC, PET TGA",
        "left": "center",
        "textStyle": {"fontSize": 16, "fontWeight": "normal"},
    },
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {
        "type": "plain",
        "orient": "vertical",
        "right": 12,
        "top": "middle",
        "data": [s["name"] for s in series],
    },
    "grid": {"left": 72, "right": 175, "top": 70, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": float(x_min),
        "max": float(x_max),
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisTick": {"show": True},
        "axisLabel": {"fontSize": 11},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": float(w_min - w_pad),
            "max": float(w_max + 1),
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"fontSize": 11},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "−DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": float(min(0, d_min - d_pad)),
            "max": float(d_max + d_pad),
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"fontSize": 11},
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
        "height": 520,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
