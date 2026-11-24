import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the Acid-washed sheet
df = pd.read_excel(DATA_FILE, sheet_name="Acid-washed")

# Extract data columns
temperature = df["Temperature (°C)"].tolist()
weight = df["Weight (%)"].tolist()
deriv_weight = df["Deriv. Weight (%/°C)"].tolist()

# Build ECharts option for TGA curve with minor ticks on x-axis
option = {
    "backgroundColor": "#ffffff",
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 10
    },
    "grid": {
        "left": 70,
        "right": 70,
        "top": 50,
        "bottom": 60
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "type": "value",
        "min": 30,
        "max": 900,
        "splitLine": {"show": True, "lineStyle": {"color": "#e0e0e0"}},
        "minorTick": {"show": True, "length": 4},
        "minorSplitLine": {"show": True, "lineStyle": {"color": "#f0f0f0"}},
        "axisLabel": {"formatter": "{value}"}
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "splitLine": {"show": True, "lineStyle": {"color": "#e0e0e0"}}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "value",
            "position": "right",
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "itemStyle": {"color": "#1f77b4"},
            "data": [[t, w] for t, w in zip(temperature, weight)]
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "yAxisIndex": 1,
            "lineStyle": {"width": 2, "type": "dashed"},
            "itemStyle": {"color": "#d62728"},
            "data": [[t, d] for t, d in zip(temperature, deriv_weight)]
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
