import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

sheets = [
    ("Raw", "검정", "#000000"),
    ("Acid-washed", "파랑", "#2166d1"),
    ("Annealed", "빨강", "#d62728"),
]

series = []
for sheet_name, label, color in sheets:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)
    values = df[[x_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()

    series.append({
        "name": sheet_name,
        "type": "line",
        "showSymbol": False,
        "smooth": False,
        "lineStyle": {"width": 2, "color": color},
        "itemStyle": {"color": color},
        "data": values.values.tolist(),
    })

option = {
    "animation": False,
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": [item[0] for item in sheets],
        "top": 10,
    },
    "grid": {"left": 75, "right": 30, "top": 55, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#444"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#444"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "overlaid_weight",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
