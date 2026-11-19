import pandas as pd
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")

# Extract columns based on preview info
x_data = df["Temperature (°C)"].tolist()
y1_data = df["Weight (%)"].tolist()
y2_data = df["Deriv. Weight (%/°C)"].tolist()

# Create ECharts option for TGA and DTG plots stacked vertically
option = {
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "grid": [
        {
            "left": "10%",
            "right": "5%",
            "top": "8%",
            "height": "35%"
        },
        {
            "left": "10%",
            "right": "5%",
            "bottom": "12%",
            "height": "35%"
        }
    ],
    "xAxis": [
        {
            "type": "value",
            "name": "Temperature (°C)",
            "position": "top",
            "gridIndex": 0,
            "min": min(x_data),
            "max": max(x_data),
            "axisLabel": {"show": False},
            "splitLine": {"show": True}
        },
        {
            "type": "value",
            "name": "Temperature (°C)",
            "position": "bottom",
            "gridIndex": 1,
            "min": min(x_data),
            "max": max(x_data),
            "splitLine": {"show": True}
        }
    ],
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "gridIndex": 0,
            "min": min(y1_data) - 5,
            "max": max(y1_data) + 5,
            "splitLine": {"show": True}
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "gridIndex": 1,
            "min": min(y2_data) - 0.05,
            "max": max(y2_data) + 0.05,
            "splitLine": {"show": True}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": list(zip(x_data, y1_data)),
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#5470c6"}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "xAxisIndex": 1,
            "yAxisIndex": 1,
            "data": list(zip(x_data, y2_data)),
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#ee6666"}
        }
    ]
}

output = {
    "figures": [
        {
            "name": "tga_dtg_plot",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
