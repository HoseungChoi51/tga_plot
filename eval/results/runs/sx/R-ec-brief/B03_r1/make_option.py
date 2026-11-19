import pandas as pd
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")

# Extract columns
x = df["Angular frequency (rad/s)"].tolist()
g_prime = df["Storage modulus G' (Pa)"].tolist()
g_double_prime = df["Loss modulus G'' (Pa)"].tolist()

# Build ECharts option
option = {
    "title": {
        "text": "Rheology",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis"
    },
    "legend": {
        "data": ["G'", "G''"],
        "top": 30
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "log",
        "name": "Angular frequency (rad/s)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "formatter": "{value}"
        }
    },
    "yAxis": [
        {
            "type": "log",
            "name": "G' (Pa)",
            "position": "left",
            "axisLine": {"lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"color": "#1f4e9c"}
        },
        {
            "type": "log",
            "name": "G'' (Pa)",
            "position": "right",
            "axisLine": {"lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"color": "#c0392b"}
        }
    ],
    "series": [
        {
            "name": "G'",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[xi, yi] for xi, yi in zip(x, g_prime)],
            "lineStyle": {"color": "#1f4e9c"},
            "itemStyle": {"color": "#1f4e9c"}
        },
        {
            "name": "G''",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[xi, yi] for xi, yi in zip(x, g_double_prime)],
            "lineStyle": {"color": "#c0392b"},
            "itemStyle": {"color": "#c0392b"}
        }
    ]
}

output = {
    "figures": [
        {
            "name": "rheology",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
