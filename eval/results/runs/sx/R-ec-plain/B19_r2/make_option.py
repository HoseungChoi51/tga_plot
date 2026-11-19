import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Load PVC sheet
df_pvc = pd.read_excel(DATA_FILE, sheet_name="PVC")

# Rename columns for easier access if needed, but we know them from preview:
# B: Temperature (°C), C: Weight (%)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"

# Filter data between 200 and 400 °C
mask = (df_pvc[temp_col] >= 200) & (df_pvc[temp_col] <= 400)
df_filtered = df_pvc[mask].copy()

if not df_filtered.empty:
    # Get weight at start (~200°C) and end (~400°C) of the range
    # We find the closest points to 200 and 400 within the filtered set or original set near boundaries
    # To be precise, let's take the first point >= 200 and last point <= 400 in the sorted temperature list
    
    # Sort by temperature just in case
    df_sorted = df_pvc.sort_values(by=temp_col)
    
    # Find index closest to 200
    idx_200 = (df_sorted[temp_col] - 200).abs().idxmin()
    temp_200 = df_sorted.loc[idx_200, temp_col]
    weight_200 = df_sorted.loc[idx_200, weight_col]
    
    # Find index closest to 400
    idx_400 = (df_sorted[temp_col] - 400).abs().idxmin()
    temp_400 = df_sorted.loc[idx_400, temp_col]
    weight_400 = df_sorted.loc[idx_400, weight_col]
    
    mass_loss_pct = weight_200 - weight_400
else:
    mass_loss_pct = 0.0
    temp_200 = 200
    weight_200 = None
    temp_400 = 400
    weight_400 = None

# Prepare data for ECharts
# We want to plot the TGA curve for PVC (Weight vs Temp) and highlight the region 200-400°C
# Series 1: The main TGA curve
x_data = df_pvc[temp_col].tolist()
y_data = df_pvc[weight_col].tolist()

# Create a series specifically for the highlighted area (200-400°C) to show the drop clearly
# Or simply use markArea/markLine on the main series. 
# Using markArea is cleaner for highlighting a range.

option = {
    "title": {
        "text": f"PVC TGA Curve (Mass Loss 200-400°C: {mass_loss_pct:.2f}%)",
        "subtext": "Highlighting mass decrease between 200°C and 400°C",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}<br/>{b}: {c}%"
    },
    "legend": {
        "data": ["Weight (%)"],
        "top": "10%"
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": 0,
        "max": 100
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "data": [[t, w] for t, w in zip(x_data, y_data)],
            "markArea": {
                "silent": True,
                "itemStyle": {
                    "color": "rgba(255, 0, 0, 0.1)"
                },
                "data": [
                    [
                        {"xAxis": 200},
                        {"xAxis": 400}
                    ]
                ]
            },
            "markLine": {
                "silent": True,
                "symbol": "none",
                "label": {
                    "position": "start",
                    "formatter": "{b}"
                },
                "data": [
                    {"xAxis": 200, "label": {"formatter": "200°C"}},
                    {"xAxis": 400, "label": {"formatter": "400°C"}}
                ],
                "lineStyle": {
                    "type": "dashed",
                    "color": "#888"
                }
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

print(json.dumps(output))
