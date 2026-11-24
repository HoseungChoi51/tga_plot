import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

# Identify columns based on preview: Temperature (B), Weight(%) (C)
# We assume standard column names from the preview
temp_col = 'Temperature'
weight_col = 'Weight(%)'

if temp_col not in df.columns or weight_col not in df.columns:
    # Fallback to positional if names differ slightly but structure is same
    # Based on preview: A=Time, B=Temp, C=Weight, D=DW
    cols = df.columns.tolist()
    if len(cols) >= 3:
        temp_col = cols[1]
        weight_col = cols[2]

x_data = df[temp_col].dropna().tolist()
y_data = df[weight_col].dropna().tolist()

# Calculate Residue at nearest 800°C
target_temp = 800.0
residue_val = None
residue_temp = None

if len(x_data) > 0 and len(y_data) > 0:
    temps = np.array(x_data)
    weights = np.array(y_data)
    
    # Find index closest to 800
    idx_800 = np.argmin(np.abs(temps - target_temp))
    residue_temp = temps[idx_800]
    residue_val = weights[idx_800]

# Prepare ECharts Option
option = {
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "top": "5%",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{b}<br/>Temp: {a} °C<br/>Weight: {c} %"
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "top": "20%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLine": {"lineStyle": {"color": "#333"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLine": {"lineStyle": {"color": "#333"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": [[t, w] for t, w in zip(x_data, y_data)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": []
            },
            "markLine": {
                "data": []
            }
        }
    ]
}

# Add Residue Marker if found
if residue_val is not None:
    option["series"][0]["markPoint"]["data"].append({
        "coord": [float(residue_temp), float(residue_val)],
        "value": f"Residue {residue_val:.1f}%",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "position": "top",
            "formatter": f"Residue {residue_val:.1f}%",
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12,
            "color": "#1f4e9c"
        }
    })

figure = {
    "name": "plot1",
    "option": option,
    "width": 614,
    "height": 442,
    "dpi": 300,
    "formats": ["png"]
}

output = {"figures": [figure]}
print(json.dumps(output, ensure_ascii=False))
