import pandas as pd
import json

# Read the CSV file
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")

# Extract columns
x_data = df["Angular frequency (rad/s)"].tolist()
g_prime = df["Storage modulus G' (Pa)"].tolist()
g_double_prime = df["Loss modulus G'' (Pa)"].tolist()

# Prepare data for ECharts: [x, y] pairs
series_g_prime = [[x, y] for x, y in zip(x_data, g_prime)]
series_g_double_prime = [[x, y] for x, y in zip(x_data, g_double_prime)]

option = {
    "title": {
        "text": "Rheology",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        }
    },
    "tooltip": {
        "trigger": "axis"
    },
    "legend": {
        "data": ["G'", "G''"],
        "top": 30,
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "top": "18%"
    },
    "xAxis": {
        "type": "log",
        "name": "Angular frequency (rad/s)",
        "nameLocation": "middle",
        "nameGap": 30,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed",
                "color": "#ccc"
            }
        }
    },
    "yAxis": [
        {
            "type": "log",
            "name": "G' (Pa)",
            "position": "left",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            }
        },
        {
            "type": "log",
            "name": "G'' (Pa)",
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "G'",
            "type": "line",
            "data": series_g_prime,
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 6,
            "lineStyle": {
                "width": 2,
                "color": "#1f4e9c"
            },
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "yAxisIndex": 0
        },
        {
            "name": "G''",
            "type": "line",
            "data": series_g_double_prime,
            "smooth": False,
            "symbol": "circle",
            "symbolSize": 6,
            "lineStyle": {
                "width": 2,
                "color": "#c0392b"
            },
            "itemStyle": {
                "color": "#c0392b"
            },
            "yAxisIndex": 1
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

print(json.dumps(output, ensure_ascii=False))
