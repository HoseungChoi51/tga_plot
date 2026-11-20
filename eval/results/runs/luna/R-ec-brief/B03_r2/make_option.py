import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

x_col = "Angular frequency (rad/s)"
y1_col = "Storage modulus G' (Pa)"
y2_col = "Loss modulus G'' (Pa)"

data = df[[x_col, y1_col, y2_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data[(data[x_col] > 0) & (data[y1_col] > 0) & (data[y2_col] > 0)].sort_values(x_col)

option = {
    "title": {
        "text": "Rheology",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["G'", "G''"], "left": "center", "top": 32},
    "grid": {"left": 76, "right": 76, "top": 86, "bottom": 64},
    "xAxis": {
        "type": "log",
        "name": "Angular frequency (rad/s)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "log",
            "name": "Storage modulus G' (Pa)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True}
        },
        {
            "type": "log",
            "name": "Loss modulus G'' (Pa)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "G'",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": True,
            "symbolSize": 5,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "data": [[float(x), float(y)] for x, y in zip(data[x_col], data[y1_col])]
        },
        {
            "name": "G''",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": True,
            "symbolSize": 5,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "data": [[float(x), float(y)] for x, y in zip(data[x_col], data[y2_col])]
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "rheology",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
