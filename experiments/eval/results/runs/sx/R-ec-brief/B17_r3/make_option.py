import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

# Define colors for each sheet
colors = ['#1f4e9c', '#2ecc71', '#8e44ad']  # Blue, Green, Purple

series_list = []
legend_data = []

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Identify columns based on standard TGA format
    temp_col = None
    weight_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and 'deriv' not in col_lower and 'dtg' not in col_lower:
            weight_col = col
    
    if temp_col is None or weight_col is None:
        continue
        
    temps = df[temp_col].values
    weights = df[weight_col].values
    
    # Apply offset: shift each subsequent curve up by 20%
    # PE (index 0): no offset
    # PVC (index 1): +20%
    # PET (index 2): +40%
    offset = i * 20.0
    weights_offset = weights + offset
    
    # Create series data as list of [x, y] pairs
    data_pairs = [[float(t), float(w)] for t, w in zip(temps, weights_offset)]
    
    series_list.append({
        "name": sheet_name,
        "type": "line",
        "data": data_pairs,
        "smooth": False,
        "symbol": "none",
        "lineStyle": {
            "width": 2,
            "color": colors[i % len(colors)]
        },
        "emphasis": {
            "focus": "series"
        }
    })
    
    legend_data.append(sheet_name)

# Determine axis ranges
all_temps = []
all_weights_offset = []
for s in series_list:
    for pair in s['data']:
        all_temps.append(pair[0])
        all_weights_offset.append(pair[1])

min_temp = min(all_temps)
max_temp = max(all_temps)
min_weight = min(all_weights_offset)
max_weight = max(all_weights_offset)

# Add some padding to axes
y_min = min_weight - 5
y_max = max_weight + 5

option = {
    "title": {
        "text": "TGA Curves with Offset",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}: ({b}, {c})"
    },
    "legend": {
        "data": legend_data,
        "top": "5%",
        "right": "5%",
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
        "min": min_temp,
        "max": max_temp,
        "axisLine": {"onZero": False},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%) (Offset Applied)",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": y_min,
        "max": y_max,
        "axisLine": {"onZero": False},
        "splitLine": {"show": True, "lineStyle": {"type": "dashed"}},
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": series_list
}

output = {
    "figures": [
        {
            "name": "tga_offset_comparison",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
