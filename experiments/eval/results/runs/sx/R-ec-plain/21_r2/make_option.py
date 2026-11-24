import pandas as pd
import json

# Load the data from the specified Excel file
file_path = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1", header=7)  # Header is at row index 7 (8th row in 1-based indexing)

# Extract relevant columns
x_data = df["Temperature"].dropna().tolist()
y1_data = df["Weight(%)"].dropna().tolist()
y2_data = df["D.W(%/C)"].dropna().tolist()

# Ensure all series have the same length by truncating to the minimum length
min_len = min(len(x_data), len(y1_data), len(y2_data))
x_data = x_data[:min_len]
y1_data = y1_data[:min_len]
y2_data = y2_data[:min_len]

# Create ECharts option
option = {
    "title": {
        "text": "TGA Data Visualization",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis"
    },
    "legend": {
        "data": ["Weight (%)", "D.W (%/C)"],
        "top": "5%"
    },
    "grid": {
        "left": "3%",
        "right": "4%",
        "bottom": "3%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "position": "bottom"
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left"
        },
        {
            "type": "value",
            "name": "D.W (%/C)",
            "position": "right"
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": [[x, y1] for x, y1 in zip(x_data, y1_data)],
            "yAxisIndex": 0
        },
        {
            "name": "D.W (%/C)",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": [[x, y2] for x, y2 in zip(x_data, y2_data)],
            "yAxisIndex": 1
        }
    ]
}

# Prepare the final JSON output
output = {
    "figures": [
        {
            "name": "tga_plot",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
