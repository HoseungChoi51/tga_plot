import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")
df.columns = [str(c).strip() for c in df.columns]

x_col = "Temperature (°C)"
weight_col = "Weight (%)"
heat_flow_col = "Heat Flow (W/g)"

data = df[[x_col, weight_col, heat_flow_col]].apply(pd.to_numeric, errors="coerce").dropna()
x = data[x_col].tolist()
weight = data[weight_col].tolist()
heat_flow = data[heat_flow_col].tolist()

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["Weight (%)", "Heat Flow (W/g)"],
        "top": 10
    },
    "grid": {
        "left": 80,
        "right": 85,
        "top": 55,
        "bottom": 70
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLabel": {"hideOverlap": True},
        "splitLine": {"show": False}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 55,
            "axisLine": {"show": True},
            "splitLine": {"show": True}
        },
        {
            "type": "value",
            "name": "Heat flow (W/g)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLine": {"show": True},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": [[xx, yy] for xx, yy in zip(x, weight)],
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"}
        },
        {
            "name": "Heat Flow (W/g)",
            "type": "line",
            "data": [[xx, yy] for xx, yy in zip(x, heat_flow)],
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"}
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "tga_heat_flow",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
