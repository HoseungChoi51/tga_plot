import json

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

x_col = "Angular frequency (rad/s)"
g_storage_col = "Storage modulus G' (Pa)"
g_loss_col = "Loss modulus G'' (Pa)"

data = df[[x_col, g_storage_col, g_loss_col]].apply(pd.to_numeric, errors="coerce")
data = data.dropna()
data = data[(data[x_col] > 0) & (data[g_storage_col] > 0) & (data[g_loss_col] > 0)]
data = data.sort_values(x_col)

option = {
    "animation": False,
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["G' (저장 탄성률)", "G'' (손실 탄성률)"],
        "top": 12,
    },
    "grid": {
        "left": 78,
        "right": 78,
        "top": 58,
        "bottom": 68,
    },
    "xAxis": {
        "type": "log",
        "name": "Angular frequency (rad/s)",
        "nameLocation": "middle",
        "nameGap": 42,
        "logBase": 10,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
    },
    "yAxis": [
        {
            "type": "log",
            "name": "G' (Pa)",
            "nameLocation": "middle",
            "nameGap": 55,
            "logBase": 10,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
        },
        {
            "type": "log",
            "name": "G'' (Pa)",
            "nameLocation": "middle",
            "nameGap": 55,
            "logBase": 10,
            "position": "right",
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "G' (저장 탄성률)",
            "type": "line",
            "yAxisIndex": 0,
            "data": data[[x_col, g_storage_col]].values.tolist(),
            "showSymbol": True,
            "symbolSize": 6,
            "lineStyle": {"width": 2, "color": "#2563eb"},
            "itemStyle": {"color": "#2563eb"},
        },
        {
            "name": "G'' (손실 탄성률)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data[[x_col, g_loss_col]].values.tolist(),
            "showSymbol": True,
            "symbolSize": 6,
            "lineStyle": {"width": 2, "color": "#dc2626"},
            "itemStyle": {"color": "#dc2626"},
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "rheology_moduli",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
