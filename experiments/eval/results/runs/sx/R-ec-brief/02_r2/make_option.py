import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal")

# Extract columns: B=Temperature (x), C=Weight(%) (y1), D=D.W(%/C) (y2)
temp = df["Temperature"].values
weight = df["Weight(%)"].values
dtg = df["D.W(%/C)"].values

# Prepare data for ECharts
# x-axis: Temperature (0 to 900, step 200)
# y1: Weight (%)
# y2: DTG (%/C) * -1 so peaks point up

# Filter out NaN values if any
mask = ~(np.isnan(temp) | np.isnan(weight) | np.isnan(dtg))
temp_clean = temp[mask]
weight_clean = weight[mask]
dtg_clean = dtg[mask]

# Calculate residue at nearest 800°C
idx_800 = np.argmin(np.abs(temp_clean - 800))
residue_val = weight_clean[idx_800]
temp_at_residue = temp_clean[idx_800]
residue_text = f"Residue {residue_val:.1f}%"

# Find max DTG peak above 150°C
mask_peak = temp_clean > 150
if np.any(mask_peak):
    dtg_for_peak = dtg_clean[mask_peak]
    temp_for_peak = temp_clean[mask_peak]
    # Max of negative DTG means most mass loss rate. We want the peak of -DTG.
    # So we look for min(DTG) in original, which corresponds to max(-DTG).
    idx_min_dtg = np.argmin(dtg_for_peak)
    peak_temp = temp_for_peak[idx_min_dtg]
    peak_dtg_orig = dtg_for_peak[idx_min_dtg]
else:
    peak_temp = None
    peak_dtg_orig = None

peak_text = f"{peak_temp:.0f} °C" if peak_temp is not None else "No Peak"

# Series data
data_weight = [[float(t), float(w)] for t, w in zip(temp_clean, weight_clean)]
data_dtg = [[float(t), float(d * -1)] for t, d in zip(temp_clean, dtg_clean)]

# Axis ranges and ticks
# X: 0 to 900, interval 200
# Y1: Auto or reasonable range based on data. Min ~7.9, Max 100. Let's set min 0, max 100 or auto.
# User asked for "weight는 20단위로 해주고" -> This likely refers to tick interval or grid lines? 
# Usually TGA plots have y-axis starting near 0 or 100 down to residue. 
# "weight는 20단위로" -> Tick interval 20? Or axis range steps? Given context of other requests (Temperature 200 units, Deriv.Weight 0.2 units), it implies tick intervals.
# However, standard TGA y-axis often goes 0-100 or similar. If tick interval is 20, ticks would be 0, 20, 40, 60, 80, 100.
# Let's assume tick interval 20 for Y1.
# Y2: DTG * -1. Original min -1.027, max 0.0025. Negated: min -0.0025, max 1.027. 
# User said "Deriv.Weight는 0.2단위로 표시해줘". Tick interval 0.2.
# Range for Y2: Need to cover approx -0.1 to 1.1. Let's say min -0.2, max 1.2 with interval 0.2.

option = {
    "title": {
        "text": "1006R1-V normal",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["Weight (%)", "DTG (-%/\u00b0C)"],
        "top": 30,
        "left": "center",
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
        "name": "Temperature (\u00b0C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 0,
        "max": 900,
        "interval": 200,
        "axisLabel": {
            "formatter": "{value}",
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {"type": "dashed"}
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "position": "left",
            "min": 0,
            "max": 100,
            "interval": 20,
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": True,
                "lineStyle": {"type": "dashed"}
            }
        },
        {
            "type": "value",
            "name": "DTG (-%/C)",
            "nameLocation": "middle",
            "nameGap": 40,
            "position": "right",
            "min": -0.2,
            "max": 1.2,
            "interval": 0.2,
            "axisLabel": {
                "formatter": "{value}",
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
            "yAxisIndex": 0,
            "data": data_weight,
            "showSymbol": False,
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "symbolSize": 8,
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "label": {
                    "show": True,
                    "formatter": residue_text,
                    "position": "right",
                    "distance": 5,
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12
                },
                "data": [
                    {
                        "coord": [float(temp_at_residue), float(residue_val)],
                        "symbol": "circle"
                    }
                ]
            }
        },
        {
            "name": "DTG (-%/C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_dtg,
            "showSymbol": False,
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            },
            "markPoint": {
                "symbolSize": 8,
                "itemStyle": {
                    "color": "#c0392b"
                },
                "label": {
                    "show": True,
                    "formatter": peak_text,
                    "position": "top",
                    "distance": 5,
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12
                },
                "data": []
            }
        }
    ]
}

# Add peak marker if found
if peak_temp is not None:
    # The value plotted is -dtg. The peak in the plot is the maximum of -dtg.
    # Which corresponds to the minimum of original dtg.
    # We already calculated peak_temp based on min(original dtg).
    # We need the corresponding y-value in the series, which is -peak_dtg_orig.
    peak_y_val = -peak_dtg_orig
    
    option["series"][1]["markPoint"]["data"] = [
        {
            "coord": [float(peak_temp), float(peak_y_val)],
            "symbol": "triangle"
        }
    ]

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
