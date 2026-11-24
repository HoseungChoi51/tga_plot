import pandas as pd
import numpy as np
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")

# Clean column names to match exactly what's in the preview if needed, 
# but usually pandas reads them as is. Let's ensure we use the right columns.
# Columns: 'Time (min)', 'Temperature (°C)', 'Weight (%)', 'Deriv. Weight (%/°C)', 'Heat Flow (W/g)'

temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
deriv_weight = df['Deriv. Weight (%/°C)'].values

# Define regions for marking
regions = [
    {"name": "H2O", "start": 120, "end": 250, "color": "#FFB6C1"}, # Light Pink
    {"name": "CO", "start": 430, "end": 580, "color": "#ADD8E6"},  # Light Blue
    {"name": "CO2", "start": 640, "end": 830, "color": "#90EE90"}   # Light Green
]

# Prepare series data
series_data = []

# TGA Curve (Weight %)
tga_series = {
    "name": "Weight (%)",
    "type": "line",
    "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
    "smooth": False,
    "symbol": "none",
    "yAxisIndex": 0,
    "lineStyle": {"width": 2},
    "itemStyle": {"color": "#1f77b4"}
}

# DTG Curve (Deriv. Weight %/°C)
dtg_series = {
    "name": "Deriv. Weight (%/°C)",
    "type": "line",
    "data": [[float(t), float(dw)] for t, dw in zip(temp, deriv_weight)],
    "smooth": False,
    "symbol": "none",
    "yAxisIndex": 1,
    "lineStyle": {"width": 1, "type": "dashed"},
    "itemStyle": {"color": "#ff7f0e"}
}

series_data.append(tga_series)
series_data.append(dtg_series)

# Add markArea and markText for each region on the first series (TGA)
mark_area_data = []
mark_text_data = []

for r in regions:
    # Mark Area: [[{xAxis: start, itemStyle: {...}}, {xAxis: end}], ...]
    mark_area_data.append([
        {
            "xAxis": r["start"],
            "itemStyle": {
                "color": r["color"],
                "opacity": 0.3
            }
        },
        {
            "xAxis": r["end"]
        }
    ])
    
    # Mark Text: Place at center of region, slightly above the curve or fixed position
    # To find a good Y position, we can look at the max weight in that range or just place it high enough
    mask = (temp >= r["start"]) & (temp <= r["end"])
    if len(weight[mask]) > 0:
        y_pos = np.max(weight[mask]) + 5 # Slightly above the highest point in this region
    else:
        y_pos = 90
        
    mark_text_data.append({
        "coord": [(r["start"] + r["end"]) / 2, y_pos],
        "value": r["name"],
        "style": {
            "font": "bold 14px Noto Sans CJK KR",
            "fill": "#333"
        }
    })

# Attach marks to the TGA series
tga_series["markArea"] = {
    "silent": True,
    "data": mark_area_data
}
tga_series["markText"] = {
    "data": mark_text_data
}

# Build ECharts Option
option = {
    "title": {
        "text": "TGA/DTG Analysis",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 30
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
        "min": 0,
        "max": 950
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "min": 30,
            "max": 105
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "position": "right",
            "min": -0.6,
            "max": 0.1
        }
    ],
    "series": series_data
}

result = {
    "figures": [
        {
            "name": "tga_plot",
            "option": option,
            "width": 800,
            "height": 500,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
