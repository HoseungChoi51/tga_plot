import pandas as pd
import json

# Read the specific sheet from the Excel file
file_path = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
sheet_name = "1006R1-V normal"

# Load data
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Extract columns based on the preview info
# X: Temperature (Column B), Y1: Weight(%) (Column C), Y2: D.W(%/C) (Column D)
x_data = df['Temperature'].tolist()
y1_data = df['Weight(%)'].tolist()
y2_data = df['D.W(%/C)'].tolist()

# Prepare ECharts option
option = {
    "title": {
        "text": "CNT 산화 거동",
        "left": "center",
        "textStyle": {
            "fontSize": 18,
            "color": "#00008B"  # Navy Blue
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Derivative Weight (%/°C)"],
        "top": 40
    },
    "grid": {
        "left": "3%",
        "right": "4%",
        "bottom": "3%",
        "containLabel": True
    },
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "type": "value",
            "min": 30,
            "max": 900,
            "splitLine": {
                "show": False
            }
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "min": 0,
            "max": 105,
            "position": "left"
        },
        {
            "name": "Derivative Weight (%/°C)",
            "type": "value",
            "position": "right",
            "offset": 0,
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
                "color": "#007ACC"
            },
            "itemStyle": {
                "color": "#007ACC"
            },
            "data": [[x, y] for x, y in zip(x_data, y1_data)]
        },
        {
            "name": "Derivative Weight (%/°C)",
            "type": "line",
            "smooth": True,
            "symbol": "none",
            "yAxisIndex": 1,
            "lineStyle": {
                "width": 2,
                "color": "#FF5722"
            },
            "itemStyle": {
                "color": "#FF5722"
            },
            "data": [[x, y] for x, y in zip(x_data, y2_data)]
        }
    ]
}

# Construct the final JSON output
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

print(json.dumps(output))
