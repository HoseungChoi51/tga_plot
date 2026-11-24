import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

# Read the Excel file
df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")

# Extract columns
temperature = df["Temperature (°C)"].tolist()
weight_percent = df["Weight (%)"].tolist()
heat_flow = df["Heat Flow (W/g)"].tolist()

# Build ECharts option
option = {
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Heat flow (W/g)"],
        "top": 10
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "12%",
        "containLabel": True
    },
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "nameLocation": "center",
            "nameGap": 30,
            "type": "value",
            "min": min(temperature),
            "max": max(temperature),
            "splitLine": {"show": False}
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "center",
            "nameGap": 45,
            "type": "value",
            "position": "left",
            "splitLine": {"lineStyle": {"type": "dashed"}}
        },
        {
            "name": "Heat flow (W/g)",
            "nameLocation": "center",
            "nameGap": 45,
            "type": "value",
            "position": "right",
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temperature, weight_percent)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "itemStyle": {"color": "#5470c6"}
        },
        {
            "name": "Heat flow (W/g)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[t, hf] for t, hf in zip(temperature, heat_flow)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "itemStyle": {"color": "#ee6666"}
        }
    ]
}

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

print(json.dumps(result))
