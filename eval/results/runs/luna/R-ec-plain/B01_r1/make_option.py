import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)

data = []
for x, y in zip(df[temperature_col], df[weight_col]):
    if pd.notna(x) and pd.notna(y):
        data.append([float(x), float(y)])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
    "grid": {"left": 76, "right": 28, "top": 78, "bottom": 62},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 950,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#333"},
        "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 35,
        "max": 102,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#333"},
        "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"color": "#333333", "width": 1.8},
            "emphasis": {"disabled": True},
            "markArea": {
                "silent": True,
                "label": {
                    "show": True,
                    "position": "top",
                    "color": "#333333",
                    "fontSize": 14,
                    "fontWeight": "bold",
                },
                "data": [
                    [
                        {"name": "H₂O", "xAxis": 120, "itemStyle": {"color": "rgba(76, 158, 217, 0.19)"}},
                        {"xAxis": 250},
                    ],
                    [
                        {"name": "CO", "xAxis": 430, "itemStyle": {"color": "rgba(93, 181, 126, 0.19)"}},
                        {"xAxis": 580},
                    ],
                    [
                        {"name": "CO₂", "xAxis": 640, "itemStyle": {"color": "rgba(231, 153, 77, 0.20)"}},
                        {"xAxis": 830},
                    ],
                ],
            },
        }
    ],
}

print(json.dumps({
    "figures": [
        {
            "name": "caox_mass_loss",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}, ensure_ascii=False))
