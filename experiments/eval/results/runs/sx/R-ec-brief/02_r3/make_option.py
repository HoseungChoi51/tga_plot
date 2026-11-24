import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal")

# Extract columns based on user request: B=Temperature(X), C=Weight(Y1), D=D.W(Y2)
x_col = df.columns[1]  # Column B: Temperature
y1_col = df.columns[2] # Column C: Weight(%)
y2_col = df.columns[3] # Column D: D.W(%/C)

temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Prepare data for ECharts
# Series 1: Weight (Left Y axis)
data_weight = [[float(t), float(w)] for t, w in zip(temp, weight)]

# Series 2: DTG (Right Y axis), multiplied by -1 so peaks point up
data_dtg = [[float(t), float(-d)] for t, d in zip(temp, dtg)]

# Find Residue at nearest to 800°C
idx_800 = np.argmin(np.abs(temp - 800))
residue_temp = temp[idx_800]
residue_val = weight[idx_800]
residue_label_text = f"Residue {residue_val:.1f}%"

# Find Max DTG peak above 150°C
mask_above_150 = temp > 150
if np.any(mask_above_150):
    dtg_above_150 = dtg[mask_above_150]
    temp_above_150 = temp[mask_above_150]
    
    # We want the highest peak of the *negative* DTG values? 
    # The user says "Deriv.Weight 의 max값을 표시해주고". 
    # In TGA plots, DTG is negative during mass loss. Usually "peak" refers to the maximum rate of loss, which is the most negative value (minimum).
    # However, the prompt instructions say: "peak: the temperature of the highest DTG peak above 150 °C".
    # And standard practice: DTG plotted as -DTG makes peaks positive.
    # Let's look at the instruction: "right y axis ... multiplied by -1 so its peaks point up".
    # So we plot -DTG. The "highest DTG peak" in the context of the visual plot (where peaks point up) corresponds to the minimum original DTG value.
    # But strictly speaking, if the user asks for "max value of Deriv.Weight", and Deriv.Weight is negative, the max is close to 0. That's likely not what they mean. They mean the peak magnitude.
    # Instruction: "peak: the temperature of the highest DTG peak above 150 °C". This usually implies the local maximum of the derivative curve (magnitude).
    # Given the inversion (-1), the visual peak is at min(original_DTG).
    
    min_dtg_idx_local = np.argmin(dtg_above_150) # Most negative = largest mass loss rate
    peak_temp = temp_above_150[min_dtg_idx_local]
    peak_val_original = dtg_above_150[min_dtg_idx_local]
    peak_val_plotted = -peak_val_original
    
    peak_label_text = f"{int(round(peak_temp))} °C"
else:
    peak_temp = None
    peak_val_plotted = 0
    peak_label_text = ""

# Construct Markers
markers = []
# Marker for Residue
markers.append({
    "coord": [float(residue_temp), float(residue_val)],
    "value": residue_label_text,
    "symbol": "circle",
    "symbolSize": 8,
    "itemStyle": {"color": "#1f4e9c"},
    "label": {
        "show": True,
        "position": "top",
        "formatter": "{b}",
        "fontSize": 12,
        "color": "#1f4e9c",
        "fontWeight": "bold"
    }
})

# Marker for Peak
if peak_temp is not None:
    markers.append({
        "coord": [float(peak_temp), float(peak_val_plotted)],
        "value": peak_label_text,
        "symbol": "diamond",
        "symbolSize": 10,
        "itemStyle": {"color": "#c0392b"},
        "label": {
            "show": True,
            "position": "top",
            "formatter": "{b}",
            "fontSize": 12,
            "color": "#c0392b",
            "fontWeight": "bold"
        }
    })

# Axis Ranges and Intervals
# X-axis: Temperature 0 to 900 (data goes to 900), interval 200
x_min = 0
x_max = 900
x_interval = 200

# Y1-axis: Weight 0 to 100 (or slightly more), interval 20
y1_min = 0
y1_max = 100
y1_interval = 20

# Y2-axis: DTG. Data range roughly -1.0 to 0.0. Plotted as -DTG -> 0.0 to 1.0.
# Interval 0.2. Range should cover the max plotted value.
if len(data_dtg) > 0:
    max_plotted_dtg = max(item[1] for item in data_dtg)
else:
    max_plotted_dtg = 1.0

y2_min = 0
# Calculate a nice round max based on data
calculated_y2_max = np.ceil(max_plotted_dtg / 0.2) * 0.2
if calculated_y2_max < 0.2:
    calculated_y2_max = 0.2
y2_max = calculated_y2_max + 0.2 # Add some padding
y2_interval = 0.2

option = {
    "title": {
        "text": "1006R1-V normal",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16,
            "fontWeight": "bold"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
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
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "min": x_min,
        "max": x_max,
        "interval": x_interval,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "splitLine": {
            "show": False
        },
        "axisLine": {
            "lineStyle": {
                "color": "#333"
            }
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "min": y1_min,
            "max": y1_max,
            "interval": y1_interval,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed",
                    "color": "#ccc"
                }
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#1f4e9c"
                }
            }
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "value",
            "min": y2_min,
            "max": y2_max,
            "interval": y2_interval,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "splitLine": {
                "show": False
            },
            "axisLine": {
                "lineStyle": {
                    "color": "#c0392b"
                }
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": data_weight,
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#1f4e9c"
            },
            "markPoint": {
                "data": markers
            }
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_dtg,
            "smooth": True,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#c0392b"
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
