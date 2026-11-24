import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheets = ['PE', 'PVC', 'PET']

# Colors for each polymer
colors = ['#E74C3C', '#3498DB', '#2ECC71']  # Red, Blue, Green

# We'll create offset TGA curves: PE at 0-100%, PVC at 120-220%, PET at 240-340%
# Each curve is shifted up by 20 percentage points relative to the previous one.
offsets = [0, 120, 240]

series_list = []
legend_data = []

for i, sheet_name in enumerate(sheets):
    df = pd.read_excel(xl, sheet_name=sheet_name)
    temp = df['Temperature (°C)'].values
    weight = df['Weight (%)'].values
    
    # Apply offset
    offset_weight = weight + offsets[i]
    
    # Downsample for performance (keep every 5th point or so, but ensure key points)
    step = max(1, len(temp) // 200)
    temp_sampled = temp[::step].tolist()
    offset_weight_sampled = offset_weight[::step].tolist()
    
    series_list.append({
        "name": sheet_name,
        "type": "line",
        "data": list(zip(temp_sampled, offset_weight_sampled)),
        "smooth": True,
        "symbol": "none",
        "lineStyle": {
            "width": 2,
            "color": colors[i]
        },
        "itemStyle": {
            "color": colors[i]
        }
    })
    legend_data.append(sheet_name)

option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA Weight Curves with Offset",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None  # Will use default
    },
    "legend": {
        "data": legend_data,
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": 80,
        "right": 40,
        "top": 60,
        "bottom": 60
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 0,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "color": "#e0e0e0"
            }
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%) (Offset)",
        "nameLocation": "middle",
        "nameGap": 50,
        "min": -10,
        "max": 360,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "color": "#e0e0e0"
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

print(json.dumps(result, ensure_ascii=False))
