import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the 'Raw' sheet
df = pd.read_excel(DATA_FILE, sheet_name='Raw', header=0)

# Extract columns: Temperature (°C), Weight (%), Deriv. Weight (%/°C)
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
deriv_weight = df['Deriv. Weight (%/°C)'].values

# Prepare data for ECharts: [x, y] pairs
weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
deriv_data = [[float(t), float(d)] for t, d in zip(temp, deriv_weight)]

# Build ECharts option with inverted x-axis (high temp on left)
option = {
    "title": {
        "text": "TGA - Raw",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "12%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "inverse": True,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": False
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "position": "right",
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#5470c6"
            },
            "itemStyle": {
                "color": "#5470c6"
            },
            "data": weight_data
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 1,
            "lineStyle": {
                "width": 2,
                "color": "#ee6666"
            },
            "itemStyle": {
                "color": "#ee6666"
            },
            "data": deriv_data
        }
    ]
}

result = {
    "figures": [
        {
            "name": "tga_raw_inverted",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
