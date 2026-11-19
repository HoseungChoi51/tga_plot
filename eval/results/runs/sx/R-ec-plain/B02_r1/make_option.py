import pandas as pd
import json
import numpy as np

# Load data
df = pd.read_csv("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")

# Rename columns for easier access
df.columns = ['Time', 'Temperature', 'Weight', 'Deriv_Weight', 'Heat_Flow']

# Extract relevant columns
temp = df['Temperature'].values
weight = df['Weight'].values
heat_flow = df['Heat_Flow'].values

# Identify peaks in Heat Flow
# Endothermic peaks: local maxima (positive values)
# Exothermic peaks: local minima (negative values)

from scipy.signal import find_peaks

# Find endothermic peaks (local maxima)
peaks_endo, _ = find_peaks(heat_flow, prominence=0.1) # Adjust prominence if needed to filter noise
# Filter for significant positive peaks
endo_indices = [i for i in peaks_endo if heat_flow[i] > 0.5] # Threshold for clear endothermic peak

# Find exothermic peaks (local minima)
peaks_exo, _ = find_peaks(-heat_flow, prominence=0.1)
exo_indices = [i for i in peaks_exo if heat_flow[i] < -0.5] # Threshold for clear exothermic peak

# Sort by temperature and pick top 2 endothermic and top 1 exothermic based on magnitude or position?
# The request asks for "two endothermic peaks and one exothermic peak". 
# Usually in TGA-DSC of materials like CaOx, we expect specific decomposition steps.
# Let's sort the identified indices by their absolute value of heat flow to get the most prominent ones, 
# then sort them by temperature for labeling order.

def get_top_n_indices(indices, n):
    if not indices:
        return []
    # Get values at these indices
    vals = [(i, abs(heat_flow[i])) for i in indices]
    # Sort by magnitude descending
    vals.sort(key=lambda x: x[1], reverse=True)
    # Take top n
    top_idx = [v[0] for v in vals[:n]]
    # Sort these top indices by temperature (index corresponds to time/temp order in file usually, but let's check temp array)
    # Since the file is sorted by Time/Temperature, index order is temperature order.
    top_idx.sort()
    return top_idx

top_endo_idx = get_top_n_indices(endo_indices, 2)
top_exo_idx = get_top_n_indices(exo_indices, 1)

# Prepare mark points for ECharts
mark_points = []

for idx in top_endo_idx:
    t = temp[idx]
    hf = heat_flow[idx]
    mark_points.append({
        "coord": [t, hf],
        "value": f"{t:.1f}°C",
        "itemStyle": {"color": "#FF6B6B"}, # Red-ish for endothermic
        "symbolSize": 8,
        "label": {
            "show": True,
            "position": "top",
            "formatter": "{c}",
            "fontSize": 10,
            "color": "#333"
        }
    })

for idx in top_exo_idx:
    t = temp[idx]
    hf = heat_flow[idx]
    mark_points.append({
        "coord": [t, hf],
        "value": f"{t:.1f}°C",
        "itemStyle": {"color": "#4ECDC4"}, # Teal-ish for exothermic
        "symbolSize": 8,
        "label": {
            "show": True,
            "position": "bottom",
            "formatter": "{c}",
            "fontSize": 10,
            "color": "#333"
        }
    })

# Create series data
series_weight = [[float(t), float(w)] for t, w in zip(temp, weight)]
series_hf = [[float(t), float(hf)] for t, hf in zip(temp, heat_flow)]

option = {
    "title": {
        "text": "TGA/DSC Analysis",
        "subtext": "Weight Loss and Heat Flow",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        },
        "subtextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        },
        "backgroundColor": "rgba(255, 255, 255, 0.9)",
        "borderColor": "#ccc",
        "borderWidth": 1,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "color": "#333"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Heat Flow (W/g)"],
        "top": "10%",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "scale": False,
        "min": 0,
        "max": 1000,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "lineStyle": {
                "type": "dashed",
                "color": "#eee"
            }
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "min": 30,
            "max": 105,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "lineStyle": {
                    "type": "dashed",
                    "color": "#eee"
                }
            }
        },
        {
            "name": "Heat Flow (W/g)",
            "type": "value",
            "position": "right",
            "min": -2,
            "max": 3,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": series_weight,
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "color": "#5470C6"
            },
            "areaStyle": {
                "opacity": 0.1
            }
        },
        {
            "name": "Heat Flow (W/g)",
            "type": "line",
            "yAxisIndex": 1,
            "data": series_hf,
            "smooth": True,
            "showSymbol": False,
            "lineStyle": {
                "width": 2,
                "color": "#EE6666"
            },
            "markPoint": {
                "data": mark_points
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
