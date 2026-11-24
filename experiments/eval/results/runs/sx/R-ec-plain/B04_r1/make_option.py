import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")

# Extract columns
x = df["2Theta (deg)"].values
y = df["Intensity (counts)"].values

# Find top 5 peaks
peaks, properties = find_peaks(y, prominence=10) # Use prominence to filter noise
if len(peaks) > 0:
    peak_heights = y[peaks]
    sorted_indices = np.argsort(peak_heights)[::-1][:5]
    top_5_peak_indices = peaks[sorted_indices]
    top_5_2theta = x[top_5_peak_indices]
else:
    top_5_2theta = []

# Prepare data for ECharts
data_points = [[float(xi), float(yi)] for xi, yi in zip(x, y)]

# Prepare mark points for the top 5 peaks
mark_point_data = []
for val in top_5_2theta:
    # Find the corresponding intensity for this exact 2theta value
    idx = np.where(np.isclose(x, val))[0]
    if len(idx) > 0:
        int_val = float(y[idx[0]])
        mark_point_data.append({
            "coord": [float(val), int_val],
            "value": f"{val:.2f}",
            "symbolSize": 8
        })

option = {
    "title": {
        "text": "XRD 패턴",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis"
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "15%",
        "top": "15%"
    },
    "xAxis": {
        "type": "value",
        "name": "2θ (deg)",
        "min": 10,
        "max": 80,
        "axisLabel": {
            "formatter": "{value}"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Intensity (counts)",
        "position": "left"
    },
    "series": [
        {
            "name": "Intensity",
            "type": "line",
            "showSymbol": False,
            "data": data_points,
            "smooth": True,
            "lineStyle": {
                "width": 1.5,
                "color": "#5470c6"
            },
            "markPoint": {
                "data": mark_point_data,
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{@[0]:.2f}°",
                    "fontSize": 10,
                    "color": "#333"
                },
                "itemStyle": {
                    "color": "#ee6666"
                }
            }
        }
    ]
}

output = {
    "figures": [
        {
            "name": "xrd_pattern",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
