import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")

# Extract columns
x = df["2Theta (deg)"].values
y = df["Intensity (counts)"].values

# Find peaks
# Use a reasonable prominence to avoid noise peaks
peaks, properties = find_peaks(y, prominence=50)

# Get peak intensities and sort by intensity descending
peak_indices = peaks[np.argsort(properties['prominences'])[::-1]] # Sort by prominence or height? Usually height/intensity is key for "strongest"
# Let's sort by height (intensity)
peak_intensities = y[peaks]
sorted_peak_indices = peaks[np.argsort(peak_intensities)[::-1]]

# Take top 5
top_5_indices = sorted_peak_indices[:5]
top_5_2theta = x[top_5_indices]
top_5_intensity = y[top_5_indices]

# Prepare series data for ECharts
series_data = [[float(xi), float(yi)] for xi, yi in zip(x, y)]

# Prepare mark points for the top 5 peaks
mark_points = []
for i, idx in enumerate(top_5_indices):
    mark_points.append({
        "coord": [float(x[idx]), float(y[idx])],
        "value": f"{x[idx]:.2f}",
        "symbolSize": 8,
        "label": {
            "show": True,
            "formatter": "{c}",
            "position": "top",
            "color": "#d62728"
        }
    })

option = {
    "title": {
        "text": "XRD Pattern",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "2θ (deg)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 10,
        "max": 80,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Intensity (counts)",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": [
        {
            "name": "Intensity",
            "type": "line",
            "data": series_data,
            "smooth": False,
            "lineStyle": {
                "width": 1,
                "color": "#1f77b4"
            },
            "symbol": "none",
            "markPoint": {
                "data": mark_points,
                "symbol": "circle",
                "itemStyle": {
                    "color": "#d62728"
                }
            }
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
