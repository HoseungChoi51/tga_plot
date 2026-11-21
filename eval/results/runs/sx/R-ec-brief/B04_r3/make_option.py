import pandas as pd
import numpy as np
import json

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")

x_col = "2Theta (deg)"
y_col = "Intensity (counts)"

# Prepare data for ECharts
x_data = df[x_col].values.tolist()
y_data = df[y_col].values.tolist()

# Find top 5 peaks
# Simple peak detection: local maxima with some prominence
from scipy.signal import find_peaks

peaks, properties = find_peaks(df[y_col], height=0.1*np.max(df[y_col]), distance=10)

if len(peaks) > 0:
    # Sort by intensity descending
    peak_intensities = df[y_col].iloc[peaks]
    sorted_indices = np.argsort(peak_intensities)[::-1][:5]
    top5_peak_indices = peaks[sorted_indices]
    top5_2theta = df[x_col].iloc[top5_peak_indices].tolist()
else:
    top5_2theta = []

# Build markPoint data for the top 5 peaks
mark_point_data = []
for i, idx in enumerate(top5_peak_indices):
    mark_point_data.append({
        "name": f"Peak {i+1}",
        "coord": [float(df[x_col].iloc[idx]), float(df[y_col].iloc[idx])],
        "value": f"{df[x_col].iloc[idx]:.2f}°",
        "symbolSize": 40,
        "itemStyle": {"color": "#e74c3c"},
        "label": {
            "show": True,
            "formatter": "{b}",
            "position": "top",
            "fontSize": 10,
            "color": "#333"
        }
    })

option = {
    "title": {
        "text": "XRD Pattern",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": function_placeholder if False else None  # Not using JS functions
    },
    "grid": {
        "left": "8%",
        "right": "5%",
        "bottom": "12%",
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
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"color": "#eee"}
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Intensity (counts)",
        "nameLocation": "middle",
        "nameGap": 50,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"color": "#eee"}
        }
    },
    "series": [
        {
            "name": "Intensity",
            "type": "line",
            "data": [[float(x), float(y)] for x, y in zip(x_data, y_data)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 1.5
            },
            "markPoint": {
                "data": mark_point_data
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
