import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import json

# Load data from the specified file
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
df_pvc = pd.read_excel(file_path, sheet_name="PVC")

# Extract relevant columns
temp = df_pvc["Temperature (°C)"].values
weight = df_pvc["Weight (%)"].values
deriv_weight = df_pvc["Deriv. Weight (%/°C)"].values

# Find peaks in the derivative weight to identify decomposition steps
# We look for negative peaks (since weight decreases)
# Inverting deriv_weight to make valleys into peaks for find_peaks
inverted_deriv = -deriv_weight

# Find peaks with some prominence to avoid noise
peaks, properties = find_peaks(inverted_deriv, prominence=0.1)

# Get the temperatures at these peaks
peak_temps = temp[peaks]

# Prepare ECharts option
option = {
    "title": {
        "text": "PVC TGA Curve with Decomposition Temperatures",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}: {b}<br/>{c}%"
    },
    "legend": {
        "data": ["Weight (%)", "Decomposition Points"],
        "top": 30
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "min": 30,
        "max": 900
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "min": 0,
        "max": 105
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2}
        },
        {
            "name": "Decomposition Points",
            "type": "scatter",
            "data": [[float(t), float(np.interp(t, temp, weight))] for t in peak_temps],
            "symbolSize": 10,
            "itemStyle": {"color": "red"},
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{@[0]} °C",
                "fontSize": 12,
                "color": "red"
            }
        }
    ]
}

# Construct final output
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
