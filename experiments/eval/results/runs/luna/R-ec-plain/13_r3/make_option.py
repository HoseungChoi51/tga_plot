import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")
df = df[["Temperature (°C)", "Weight (mg)"]].apply(pd.to_numeric, errors="coerce").dropna()

data = [[float(x), float(y)] for x, y in zip(df["Temperature (°C)"], df["Weight (mg)"])]

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 76, "right": 30, "top": 35, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (mg)",
        "nameLocation": "middle",
        "nameGap": 55,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "scale": True,
    },
    "series": [
        {
            "name": "Weight (mg)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"width": 2},
            "emphasis": {"focus": "series"},
        }
    ],
}

print(json.dumps({
    "figures": [{
        "name": "weight_mg_vs_temperature",
        "option": option,
        "width": 800,
        "height": 550,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False))
