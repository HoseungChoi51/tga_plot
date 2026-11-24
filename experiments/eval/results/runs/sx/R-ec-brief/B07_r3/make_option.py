import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read the second sheet (PVC)
df = pd.read_excel(DATA_FILE, sheet_name=1)

# Extract columns based on header names
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temps = df[temp_col].values
weights = df[weight_col].values
dtg = df[dtg_col].values * -1  # Multiply by -1 so peaks point up

# Function to find weight at a specific temperature (nearest point)
def get_weight_at_temp(temps, weights, target_temp):
    idx = np.argmin(np.abs(temps - target_temp))
    return temps[idx], weights[idx]

# Get weights at 300°C and 600°C
t_300, w_300 = get_weight_at_temp(temps, weights, 300)
t_600, w_600 = get_weight_at_temp(temps, weights, 600)

# Prepare data for ECharts
# TGA line: [temperature, weight]
tga_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
# DTG line: [temperature, dtg]
dtg_data = [[float(t), float(d)] for t, d in zip(temps, dtg)]

# Mark points for 300°C and 600°C
mark_points = [
    {
        "coord": [float(t_300), float(w_300)],
        "label": {
            "show": True,
            "formatter": f"{w_300:.2f}%",
            "position": "top",
            "color": "#1f4e9c",
            "fontSize": 12
        },
        "symbolSize": 8
    },
    {
        "coord": [float(t_600), float(w_600)],
        "label": {
            "show": True,
            "formatter": f"{w_600:.2f}%",
            "position": "top",
            "color": "#1f4e9c",
            "fontSize": 12
        },
        "symbolSize": 8
    }
]

option = {
    "title": {
        "text": "PVC",
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
        "data": ["Weight (%)", "DTG (%/°C)"],
        "orient": "vertical",
        "left": "5%",
        "top": "middle",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
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
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "axisLine": {"lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "color": "#1f4e9c"
            },
            "splitLine": {"show": False}
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "axisLine": {"lineStyle": {"color": "#c0392b"}},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "color": "#c0392b"
            },
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": tga_data,
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "markPoint": {
                "data": mark_points,
                "symbol": "circle"
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "itemStyle": {
                "color": "#c0392b"
            }
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
