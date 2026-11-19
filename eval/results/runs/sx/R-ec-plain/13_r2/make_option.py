import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

# Read the Excel file
df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")

# Extract data for plotting
# X-axis: Temperature (°C)
x_data = df["Temperature (°C)"].dropna().tolist()
# Y1-axis: Weight (mg)
y1_data = df["Weight (mg)"].dropna().tolist()

# Align lengths in case of NaNs causing misalignment
min_len = min(len(x_data), len(y1_data))
x_data = x_data[:min_len]
y1_data = y1_data[:min_len]

# Create ECharts option
option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA - CNT-01",
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
    "grid": {
        "left": "15%",
        "right": "10%",
        "bottom": "15%",
        "top": "15%"
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "name": "Weight (mg)",
        "nameLocation": "middle",
        "nameGap": 40,
        "type": "value",
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": [
        {
            "name": "Weight (mg)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#1f77b4"
            },
            "data": [[x, y] for x, y in zip(x_data, y1_data)]
        }
    ]
}

# Output JSON
result = {
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

print(json.dumps(result, ensure_ascii=False))
