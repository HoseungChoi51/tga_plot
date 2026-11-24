import json
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
    "legend": {"data": ["G'", "G''"], "top": 32},
    "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
    "xAxis": {
        "type": "log",
        "name": "Angular frequency (rad/s)",
        "nameLocation": "middle",
        "nameGap": 38,
        "logBase": 10,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "log",
            "name": "Storage modulus G' (Pa)",
            "nameLocation": "middle",
            "nameGap": 52,
            "logBase": 10,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "log",
            "name": "Loss modulus G'' (Pa)",
            "nameLocation": "middle",
            "nameGap": 52,
            "logBase": 10,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "G'",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": True,
            "symbolSize": 5,
            "data": data[[x_col, y1_col]].values.tolist(),
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"}
        },
        {
            "name": "G''",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": True,
            "symbolSize": 5,
            "data": data[[x_col, y2_col]].values.tolist(),
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"}
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
