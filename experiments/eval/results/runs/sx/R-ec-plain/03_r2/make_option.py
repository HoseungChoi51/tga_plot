import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V acid")

# Extract columns
temp = df["Temperature"].values
weight = df["Weight(%)"].values
dtg = df["D.W(%/C)"].values

# Filter data for x-axis range 100~800
mask = (temp >= 100) & (temp <= 800)
x_vals = temp[mask]
y1_vals = weight[mask]
y2_vals = dtg[mask]

# Find peaks in DTG (local minima since mass loss is negative)
# We need to find the two most prominent peaks
from scipy.signal import find_peaks

# Invert DTG to find peaks as maxima
inverted_dtg = -y2_vals
# Use a minimum distance and prominence to avoid noise
peaks, properties = find_peaks(inverted_dtg, distance=50, prominence=0.05)

# If we found more than 2 peaks, sort by prominence and take top 2
if len(peaks) > 2:
    peak_prominences = properties['prominences']
    sorted_indices = np.argsort(peak_prominences)[::-1][:2]
    peaks = peaks[sorted_indices]

# Prepare markPoint data for ECharts
mark_point_data = []
for idx in peaks:
    if idx < len(x_vals):
        mark_point_data.append({
            "coord": [float(x_vals[idx]), float(y2_vals[idx])],
            "value": round(float(y2_vals[idx]), 4),
            "symbolSize": 10
        })

# Build the option
option = {
    "backgroundColor": "#ffffff",
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": None  # Default formatter is fine
    },
    "legend": {
        "data": ["Weight (%)", "DTG (%/°C)"],
        "top": "5%",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
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
        "min": 100,
        "max": 800,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLine": {"lineStyle": {"color": "#5470c6"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "axisLine": {"lineStyle": {"color": "#ee6666"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": [[float(t), float(w)] for t, w in zip(x_vals, y1_vals)],
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#5470c6"},
            "itemStyle": {"color": "#5470c6"},
            "yAxisIndex": 0
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "data": [[float(t), float(d)] for t, d in zip(x_vals, y2_vals)],
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#ee6666"},
            "itemStyle": {"color": "#ee6666"},
            "yAxisIndex": 1,
            "markPoint": {
                "data": mark_point_data,
                "symbol": "pin",
                "label": {
                    "show": True,
                    "formatter": "{b}",
                    "fontSize": 10,
                    "fontFamily": "Noto Sans CJK KR"
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
