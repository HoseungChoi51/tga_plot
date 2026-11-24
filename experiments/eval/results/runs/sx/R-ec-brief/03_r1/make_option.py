import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V acid")

# Extract columns based on TGA guess
x_col = "Temperature"
y1_col = "Weight(%)"
y2_col = "D.W(%/C)"

# Prepare data
temp = df[x_col].values.astype(float)
weight = df[y1_col].values.astype(float)
dtg = df[y2_col].values.astype(float) * -1  # Multiply by -1 so peaks point up

# Filter for x-axis range 100~800 for plotting
mask_plot = (temp >= 100) & (temp <= 800)
temp_plot = temp[mask_plot]
weight_plot = weight[mask_plot]
dtg_plot = dtg[mask_plot]

# Find residue at 800 C
idx_800 = np.argmin(np.abs(temp - 800))
residue_val = float(weight[idx_800])
residue_temp = float(temp[idx_800])

# Find top 2 DTG peaks above 150 C
mask_peak_search = (temp > 150)
temp_search = temp[mask_peak_search]
dtg_search = dtg[mask_peak_search]

peak_temps = []
peak_vals = []

if len(dtg_search) > 0:
    # Get indices of top 2 values in dtg_search
    # Note: dtg here is already multiplied by -1, so we want max values
    # argsort returns ascending order, so last two are largest
    top_2_indices_local = np.argsort(dtg_search)[-2:]
    top_2_indices_global = np.where(mask_peak_search)[0][top_2_indices_local]
    
    peak_temps_raw = temp[top_2_indices_global]
    peak_vals_raw = dtg[top_2_indices_global] # These are positive values now
    
    # Sort peaks by temperature for consistent labeling order
    sort_idx = np.argsort(peak_temps_raw)
    peak_temps = [float(t) for t in peak_temps_raw[sort_idx]]
    peak_vals = [float(v) for v in peak_vals_raw[sort_idx]]

# Construct ECharts Option
option = {
    "title": {
        "text": "1006R1-V acid",
        "left": "center",
        "textStyle": {
            "fontSize": 14,
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "DTG"],
        "orient": "vertical",
        "left": "left",
        "top": "middle",
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
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": 100,
            "max": 800,
            "splitLine": {"show": False},
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "left",
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        {
            "name": "DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "type": "value",
            "position": "right",
            "splitLine": {"show": False},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[float(t), float(w)] for t, w in zip(temp_plot, weight_plot)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "showSymbol": False,
            "markPoint": {
                "data": [
                    {
                        "coord": [residue_temp, residue_val],
                        "symbolSize": 10,
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_val:.1f}%",
                            "position": "right",
                            "distance": 10,
                            "fontSize": 10,
                            "fontFamily": "Noto Sans CJK KR",
                            "color": "#1f4e9c"
                        },
                        "itemStyle": {"color": "#1f4e9c"}
                    }
                ]
            }
        },
        {
            "name": "DTG",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[float(t), float(d)] for t, d in zip(temp_plot, dtg_plot)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "showSymbol": False,
            "markPoint": {
                "data": [
                    {
                        "coord": [pt, pv],
                        "symbolSize": 10,
                        "label": {
                            "show": True,
                            "formatter": f"{pt:.0f} °C",
                            "position": "top",
                            "distance": 10,
                            "fontSize": 10,
                            "fontFamily": "Noto Sans CJK KR",
                            "color": "#c0392b"
                        },
                        "itemStyle": {"color": "#c0392b"}
                    } for pt, pv in zip(peak_temps, peak_vals)
                ]
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
