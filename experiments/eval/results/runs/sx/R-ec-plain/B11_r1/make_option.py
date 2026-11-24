import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read the PET sheet
df = pd.read_excel(DATA_FILE, sheet_name='PET')

# Extract data columns
temperature = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
deriv_weight = df['Deriv. Weight (%/°C)'].values

# Round weight to 2 decimal places for display
weight_rounded = np.round(weight, 2).tolist()

# Prepare series data: [x, y] pairs
tg_data = [[float(t), float(w)] for t, w in zip(temperature, weight_rounded)]
dtg_data = [[float(t), float(dw)] for t, dw in zip(temperature, deriv_weight)]

option = {
    "title": {
        "text": "PET 열분해",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16,
            "fontWeight": "bold"
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
        "bottom": 10,
        "left": "left",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "min": 30,
        "max": 900,
        "splitLine": {
            "show": True
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "min": 0,
            "max": 100,
            "position": "left",
            "splitLine": {
                "show": True
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 45,
            "type": "value",
            "position": "right",
            "splitLine": {
                "show": False
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "color": "#1f77b4"
            },
            "itemStyle": {
                "color": "#1f77b4"
            },
            "data": tg_data,
            "yAxisIndex": 0
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "color": "#ff7f0e"
            },
            "itemStyle": {
                "color": "#ff7f0e"
            },
            "data": dtg_data,
            "yAxisIndex": 1
        }
    ]
}

output = {
    "figures": [
        {
            "name": "plot1",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
