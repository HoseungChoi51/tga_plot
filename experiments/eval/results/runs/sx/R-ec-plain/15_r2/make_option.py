import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

series_list = []
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for idx, sheet_name in enumerate(xls.sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns: Temperature (x), Weight(%) (y1), D.W(%/C) (y2)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and '%' in col_lower:
            weight_col = col
        elif 'd.w' in col_lower or 'dtg' in col_lower:
            dtg_col = col
    
    if temp_col is None or weight_col is None:
        continue
    
    temps = df[temp_col].dropna().values.astype(float)
    weights = df[weight_col].dropna().values.astype(float)
    
    # Prepare TGA data (Weight vs Temperature)
    tga_data = [[float(t), float(w)] for t, w in zip(temps, weights)]
    
    color = colors[idx % len(colors)]
    
    # Add TGA series (Weight %) - left y-axis
    series_list.append({
        "name": f"{sheet_name} TGA",
        "type": "line",
        "data": tga_data,
        "smooth": False,
        "symbol": "none",
        "lineStyle": {"width": 2, "color": color},
        "itemStyle": {"color": color},
        "yAxisIndex": 0
    })
    
    # Add DTG series if available
    if dtg_col is not None:
        dtg_vals = df[dtg_col].dropna().values.astype(float)
        # Align lengths
        min_len = min(len(temps), len(dtg_vals))
        dtg_data = [[float(t), float(d)] for t, d in zip(temps[:min_len], dtg_vals[:min_len])]
        
        series_list.append({
            "name": f"{sheet_name} DTG",
            "type": "line",
            "data": dtg_data,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 1.5, "color": color, "type": "dashed"},
            "itemStyle": {"color": color},
            "yAxisIndex": 1
        })

option = {
    "title": {
        "text": "TGA / DTG Analysis",
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
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        }
    },
    "grid": {
        "left": 80,
        "right": 80,
        "top": 70,
        "bottom": 60
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 11
            },
            "min": 0,
            "max": 110
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 11
            }
        }
    ],
    "series": series_list
}

output = {
    "figures": [
        {
            "name": "tga_overlay",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
