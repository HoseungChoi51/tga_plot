import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

x_col = next(c for c in df.columns if "Temperature" in c)
y_col = next(c for c in df.columns if "Weight" in c)

data = [
    [float(x), float(y)]
    for x, y in zip(df[x_col], df[y_col])
    if pd.notna(x) and pd.notna(y)
]

option = {
    "animation": False,
    "title": {
        "text": "1006R1-V normal",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "grid": {
        "left": 75,
        "right": 30,
        "top": 65,
        "bottom": 65
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "axisLine": {"show": True},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "axisLine": {"show": True},
        "splitLine": {"show": True}
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"}
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_normal_weight",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
