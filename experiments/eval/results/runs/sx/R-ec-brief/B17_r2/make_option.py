import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheets_data = {}
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    # Identify columns based on the preview info
    # Assuming standard TGA column names from preview
    temp_col = None
    weight_col = None
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight (%)' in str(col):
            weight_col = col
    
    if temp_col and weight_col:
        sheets_data[sheet_name] = {
            'temp': df[temp_col].values,
            'weight': df[weight_col].values
        }

# Define colors for each sheet to distinguish them
colors = ['#1f4e9c', '#2ecc71', '#e67e22']  # Blue, Green, Orange

series_list = []
legend_data = []

# Process each sheet with offset
offset_step = 20.0
for i, (sheet_name, data) in enumerate(sheets_data.items()):
    temps = data['temp']
    weights = data['weight'].copy()
    
    # Apply offset: first sheet 0, second +20, third +40, etc.
    offset_value = i * offset_step
    shifted_weights = weights + offset_value
    
    # Create series data points [x, y]
    plot_data = [[float(t), float(w)] for t, w in zip(temps, shifted_weights)]
    
    series_list.append({
        "name": sheet_name,
        "type": "line",
        "data": plot_data,
        "showSymbol": False,
        "lineStyle": {
            "color": colors[i % len(colors)],
            "width": 2
        },
        "itemStyle": {
            "color": colors[i % len(colors)]
        }
    })
    legend_data.append(sheet_name)

# Calculate Y-axis range considering offsets
all_y_values = []
for s in series_list:
    all_y_values.extend([p[1] for p in s['data']])
y_min = min(all_y_values) - 5
y_max = max(all_y_values) + 5

option = {
    "title": {
        "text": "TGA Weight Curves (Offset)",
        "left": "center",
        "textStyle": {
            "fontSize": 16,
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}: ({b}, {c})"
    },
    "legend": {
        "data": legend_data,
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
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 30,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed"
            }
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%) + Offset",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": round(y_min),
        "max": round(y_max),
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed"
            }
        }
    },
    "series": series_list
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

print(json.dumps(result))
