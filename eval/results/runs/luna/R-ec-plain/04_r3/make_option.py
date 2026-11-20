import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal")
temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

data_weight = [
    [float(x), float(y)]
    for x, y in zip(temperature, weight)
    if pd.notna(x) and pd.notna(y)
]
data_derivative = [
    [float(x), float(y)]
    for x, y in zip(temperature, derivative)
    if pd.notna(x) and pd.notna(y)
]

option = {
    "title": {
        "text": "CNT 산화 거동",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 18,
            "color": "navy"
        }
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight(%)", "D.W(%/C)"],
        "top": 36,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {"left": 75, "right": 75, "top": 85, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "data": data_weight,
            "showSymbol": False,
            "yAxisIndex": 0,
            "lineStyle": {"width": 2}
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "data": data_derivative,
            "showSymbol": False,
            "yAxisIndex": 1,
            "lineStyle": {"width": 2}
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "cnt_oxidation_behavior",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False))
