import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

# Read data
df = pd.read_csv(DATA_FILE)

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
heat_flow = df['Heat Flow (W/g)'].values

# Find peaks in Heat Flow using scipy
from scipy.signal import find_peaks

# Endothermic peaks: positive peaks in heat flow (absorbing heat)
# Exothermic peaks: negative peaks in heat flow (releasing heat)
# We need to find distinct peaks above 150°C

# Filter for temperature > 150°C
mask = temp > 150
temp_filtered = temp[mask]
hf_filtered = heat_flow[mask]

# Find endothermic peaks (positive values) - looking for local maxima
endothermic_indices, _ = find_peaks(hf_filtered, height=0.1, distance=20)
endothermic_temps = temp_filtered[endothermic_indices]
endothermic_vals = hf_filtered[endothermic_indices]

# Sort by value descending and take top 2
if len(endothermic_temps) >= 2:
    idx_sorted_endo = np.argsort(endothermic_vals)[::-1][:2]
    endo_peak_temps = sorted(endothermic_temps[idx_sorted_endo])
else:
    # Fallback: just take the two highest if available
    if len(endothermic_temps) == 1:
        endo_peak_temps = [endothermic_temps[0]]
    else:
        endo_peak_temps = []

# Find exothermic peaks (negative values) - looking for local minima
exothermic_indices, _ = find_peaks(-hf_filtered, height=0.1, distance=20)
exothermic_temps = temp_filtered[exothermic_indices]
exothermic_vals = hf_filtered[exothermic_indices]

# Take the most prominent one (most negative)
if len(exothermic_temps) >= 1:
    idx_sorted_exo = np.argsort(exothermic_vals)[:1]
    exo_peak_temp = exothermic_temps[idx_sorted_exo[0]]
else:
    exo_peak_temp = None

# Residue at ~800°C
residue_mask = np.abs(temp - 800) < 10
if residue_mask.any():
    residue_idx = np.argmin(np.abs(temp[residue_mask] - 800)) + np.where(residue_mask)[0][0]
    residue_val = weight[residue_idx]
    residue_temp = temp[residue_idx]
else:
    # Nearest point
    residue_idx = np.argmin(np.abs(temp - 800))
    residue_val = weight[residue_idx]
    residue_temp = temp[residue_idx]

# Prepare series data
weight_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
heat_flow_data = [[float(t), float(h)] for t, h in zip(temp, heat_flow)]

# Build option
option = {
    "title": {
        "text": "caox",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        }
    },
    "tooltip": {
        "trigger": "axis"
    },
    "legend": {
        "data": ["Weight (%)", "Heat Flow (W/g)"],
        "orient": "vertical",
        "left": "left",
        "top": "middle",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "top": "15%",
        "bottom": "12%"
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 9
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"color": "#eee"}
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "position": "left",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 9
            },
            "splitLine": {
                "show": True,
                "lineStyle": {"color": "#eee"}
            }
        },
        {
            "type": "value",
            "name": "Heat Flow (W/g)",
            "nameLocation": "middle",
            "nameGap": 40,
            "position": "right",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 9
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
            "yAxisIndex": 0,
            "data": weight_data,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "showSymbol": False,
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 8,
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_val:.1f}%",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10,
                    "color": "#1f4e9c"
                },
                "data": [
                    {
                        "coord": [float(residue_temp), float(residue_val)],
                        "itemStyle": {"color": "#1f4e9c"}
                    }
                ]
            }
        },
        {
            "name": "Heat Flow (W/g)",
            "type": "line",
            "yAxisIndex": 1,
            "data": heat_flow_data,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "itemStyle": {
                "color": "#c0392b"
            },
            "showSymbol": False,
            "markPoint": {
                "symbol": "diamond",
                "symbolSize": 10,
                "label": {
                    "show": True,
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 10,
                    "color": "#c0392b"
                },
                "data": []
            }
        }
    ]
}

# Add peak markers to Heat Flow series
peak_markers = []
for i, pt in enumerate(endo_peak_temps):
    # Find nearest index in original data
    idx = np.argmin(np.abs(temp - pt))
    peak_markers.append({
        "coord": [float(temp[idx]), float(heat_flow[idx])],
        "label": {
            "formatter": f"{pt:.0f} °C\nEndo",
            "position": "top",
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 9,
            "color": "#27ae60"
        },
        "itemStyle": {"color": "#27ae60"}
    })

if exo_peak_temp is not None:
    idx = np.argmin(np.abs(temp - exo_peak_temp))
    peak_markers.append({
        "coord": [float(temp[idx]), float(heat_flow[idx])],
        "label": {
            "formatter": f"{exo_peak_temp:.0f} °C\nExo",
            "position": "bottom",
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 9,
            "color": "#e74c3c"
        },
        "itemStyle": {"color": "#e74c3c"}
    })

option["series"][1]["markPoint"]["data"] = peak_markers

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
