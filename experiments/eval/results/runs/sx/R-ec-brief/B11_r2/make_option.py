import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read only the PET sheet
df = pd.read_excel(DATA_FILE, sheet_name="PET")

# Identify columns based on standard TGA naming from preview
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

# Extract data
temps = df[temp_col].values
weights = df[weight_col].values
dtgs = df[dtg_col].values

# Calculate residue at 800°C
idx_800 = np.argmin(np.abs(temps - 800))
residue_val = weights[idx_800]
residue_temp = temps[idx_800]
residue_label = f"Residue {residue_val:.2f}%"

# Find highest DTG peak above 150°C
mask_above_150 = temps > 150
if np.any(mask_above_150):
    dtgs_filtered = dtgs[mask_above_150]
    temps_filtered = temps[mask_above_150]
    # Peak is most negative DTG value -> highest magnitude when multiplied by -1
    min_dtg_idx = np.argmin(dtgs_filtered)
    peak_temp = temps_filtered[min_dtg_idx]
    peak_dtg = dtgs_filtered[min_dtg_idx]
else:
    # Fallback if no data above 150
    min_dtg_idx = np.argmin(dtgs)
    peak_temp = temps[min_dtg_idx]
    peak_dtg = dtgs[min_dtg_idx]

peak_label = f"{peak_temp:.0f} °C"

# Prepare series data
# Weight series
weight_data = [[float(t), float(w)] for t, w in zip(temps, weights)]

# DTG series (multiplied by -1 so peaks point up)
dtg_data = [[float(t), float(-d)] for t, d in zip(temps, dtgs)]

# Marker data for residue and peak
residue_marker = [{"value": [float(residue_temp), float(residue_val)], "name": residue_label}]
peak_marker = [{"value": [float(peak_temp), float(-peak_dtg)], "name": peak_label}]

# Build ECharts option
option = {
    "title": {
        "text": "PET 열분해",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "-DTG (%/°C)", "Residue", "Peak"],
        "orient": "vertical",
        "bottom": 10,
        "left": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "top": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True
            }
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "position": "right",
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
            "data": weight_data,
            "yAxisIndex": 0,
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "lineStyle": {
                "width": 2
            },
            "showSymbol": False
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "data": dtg_data,
            "yAxisIndex": 1,
            "itemStyle": {
                "color": "#c0392b"
            },
            "lineStyle": {
                "width": 2
            },
            "showSymbol": False
        },
        {
            "name": "Residue",
            "type": "scatter",
            "data": residue_marker,
            "yAxisIndex": 0,
            "symbolSize": 8,
            "itemStyle": {
                "color": "#1f4e9c"
            },
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "distance": 5,
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            }
        },
        {
            "name": "Peak",
            "type": "scatter",
            "data": peak_marker,
            "yAxisIndex": 1,
            "symbolSize": 8,
            "itemStyle": {
                "color": "#c0392b"
            },
            "label": {
                "show": True,
                "formatter": "{b}",
                "position": "top",
                "distance": 5,
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
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

print(json.dumps(output, ensure_ascii=False))
