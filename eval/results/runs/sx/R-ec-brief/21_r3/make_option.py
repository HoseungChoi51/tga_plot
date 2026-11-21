import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"

# Read the Excel file, specifying header row index (0-based) and data start
# Header is at row 8 (1-based), so index 7 in pandas if we skip rows. 
# But pandas read_excel with header=7 reads row 8 as header.
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=7)

# Clean column names to match expected keys or just use them directly
# Columns are likely: Time, Temperature, Weight(%), D.W(%/C) based on preview
# Let's ensure we have the right columns
x_col = "Temperature"
y1_col = "Weight(%)"
y2_col = "D.W(%/C)"

# Extract data
temp = df[x_col].dropna().values
weight = df[y1_col].dropna().values
dtg = df[y2_col].dropna().values

# Ensure lengths match (they should if dropna aligned, but TGA data usually has same length)
min_len = min(len(temp), len(weight), len(dtg))
temp = temp[:min_len]
weight = weight[:min_len]
dtg = dtg[:min_len]

# Invert DTG for plotting (peaks point up)
dtg_inv = -dtg

# Calculate Residue at ~800°C
target_temp = 800.0
idx_residue = np.argmin(np.abs(temp - target_temp))
residue_val = weight[idx_residue]
residue_temp = temp[idx_residue]
residue_label = f"Residue {residue_val:.1f}%"

# Calculate Peak Temp > 150°C
mask_peak = temp > 150.0
if np.any(mask_peak):
    # Find max of inverted DTG (which corresponds to most negative original DTG)
    dtg_inv_masked = dtg_inv[mask_peak]
    temp_masked = temp[mask_peak]
    idx_max_dtg = np.argmax(dtg_inv_masked)
    peak_temp = temp_masked[idx_max_dtg]
    peak_val_inv = dtg_inv_masked[idx_max_dtg]
    peak_label = f"{peak_temp:.0f} °C"
else:
    peak_temp = None
    peak_val_inv = None
    peak_label = ""

# Prepare series data for ECharts
# Format: [[x, y], ...]
data_weight = [[float(t), float(w)] for t, w in zip(temp, weight)]
data_dtg = [[float(t), float(d)] for t, d in zip(temp, dtg_inv)]

# Markers for labels
mark_points = []
# Residue marker
mark_points.append({
    "coord": [float(residue_temp), float(residue_val)],
    "name": residue_label,
    "value": residue_label,
    "symbolSize": 8,
    "itemStyle": {"color": "#1f4e9c"},
    "label": {
        "show": True,
        "formatter": "{b}",
        "position": "right",
        "fontSize": 12,
        "color": "#1f4e9c"
    }
})

# Peak marker
if peak_temp is not None:
    mark_points.append({
        "coord": [float(peak_temp), float(peak_val_inv)],
        "name": peak_label,
        "value": peak_label,
        "symbolSize": 8,
        "itemStyle": {"color": "#c0392b"},
        "label": {
            "show": True,
            "formatter": "{b}",
            "position": "top",
            "fontSize": 12,
            "color": "#c0392b"
        }
    })

option = {
    "title": {
        "text": "Sheet1",
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
        "data": ["Weight (%)", "-DTG (%/°C)"],
        "left": "left",
        "top": "middle",
        "orient": "vertical",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
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
        "axisLine": {"lineStyle": {"color": "#333"}},
        "axisTick": {"alignWithLabel": True},
        "splitLine": {"show": False}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLine": {"lineStyle": {"color": "#1f4e9c"}},
            "axisTick": {"show": True},
            "splitLine": {"lineStyle": {"color": "#eee"}}
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "axisLine": {"lineStyle": {"color": "#c0392b"}},
            "axisTick": {"show": True},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": data_weight,
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [mp for mp in mark_points if mp["itemStyle"]["color"] == "#1f4e9c"]
            }
        },
        {
            "name": "-DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_dtg,
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "markPoint": {
                "data": [mp for mp in mark_points if mp["itemStyle"]["color"] == "#c0392b"]
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
