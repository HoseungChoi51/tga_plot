import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")
df.columns = [str(c).strip() for c in df.columns]

x_col = "Temperature (°C)"
y_col = "Weight (mg)"

data = []
for x, y in zip(df[x_col], df[y_col]):
    if pd.notna(x) and pd.notna(y):
        data.append([float(x), float(y)])

option = {
    "animation": False,
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 76, "right": 30, "top": 45, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLine": {"lineStyle": {"color": "#444"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (mg)",
        "nameLocation": "middle",
        "nameGap": 56,
        "axisLine": {"lineStyle": {"color": "#444"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "series": [
        {
            "name": "Weight (mg)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#1f77b4"},
        }
    ],
}

print(json.dumps({
    "figures": [{
        "name": "tga_weight_mg",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
