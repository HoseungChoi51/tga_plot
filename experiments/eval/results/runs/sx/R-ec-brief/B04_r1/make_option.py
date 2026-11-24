import pandas as pd
import numpy as np
import json

# Read the XRD data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")

# Extract columns
two_theta = df["2Theta (deg)"].values
intensity = df["Intensity (counts)"].values

# Find the 5 strongest peaks using scipy signal processing
from scipy.signal import find_peaks

# Find peaks with some prominence to avoid noise
peaks, properties = find_peaks(intensity, prominence=100)

# Sort peaks by intensity (height) in descending order
peak_intensities = intensity[peaks]
sorted_indices = np.argsort(peak_intensities)[::-1][:5]
top_5_peak_indices = peaks[sorted_indices]
top_5_peak_positions = two_theta[top_5_peak_indices]
top_5_peak_heights = intensity[top_5_peak_indices]

# Sort by 2-theta for display
sort_by_2theta = np.argsort(top_5_peak_positions)
final_positions = top_5_peak_positions[sort_by_2theta]
final_heights = top_5_peak_heights[sort_by_2theta]

# Prepare scatter data for peak markers
peak_data = [[float(pos), float(hgt)] for pos, hgt in zip(final_positions, final_heights)]

# Main line data
line_data = [[float(x), float(y)] for x, y in zip(two_theta, intensity)]

# Build ECharts option
option = {
    "title": {
        "text": "XRD Pattern",
        "left": "center",
        "textStyle": {
            "fontSize": 14,
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None
    },
    "grid": {
        "left": 70,
        "right": 30,
        "top": 60,
        "bottom": 50
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
            "fontSize": 10
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"color": "#e0e0e0"}
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Intensity (counts)",
        "nameLocation": "middle",
        "nameGap": 45,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"color": "#e0e0e0"}
        }
    },
    "series": [
        {
            "name": "Intensity",
            "type": "line",
            "data": line_data,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 1.5
            },
            "z": 1
        },
        {
            "name": "Top 5 Peaks",
            "type": "scatter",
            "data": peak_data,
            "symbolSize": 8,
            "itemStyle": {
                "color": "#c0392b"
            },
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{@[0]:.1f}°",
                "fontSize": 9,
                "fontFamily": "Noto Sans CJK KR",
                "color": "#c0392b",
                "distance": 5
            },
            "z": 2
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

print(json.dumps(result, ensure_ascii=False))
