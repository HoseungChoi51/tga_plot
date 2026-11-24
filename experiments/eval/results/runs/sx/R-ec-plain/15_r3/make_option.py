import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)

series_list = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on typical TGA structure
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or col == 'B':
            temp_col = col
        elif 'weight' in col_lower and '%' in col_lower and 'd.w' not in col_lower:
            weight_col = col
        elif 'd.w' in col_lower or 'dtg' in col_lower:
            dtg_col = col
    
    # Fallback to positional if names don't match well
    if temp_col is None:
        temp_col = df.columns[1]  # Column B
    if weight_col is None:
        weight_col = df.columns[2]  # Column C
    if dtg_col is None:
        dtg_col = df.columns[3]  # Column D
    
    temps = df[temp_col].dropna().tolist()
    weights = df[weight_col].dropna().tolist()
    dtgs = df[dtg_col].dropna().tolist()
    
    # Create paired data [temp, weight] and [temp, dtg]
    weight_data = [[t, w] for t, w in zip(temps, weights)]
    dtg_data = [[t, d] for t, d in zip(temps, dtgs)]
    
    series_list.append({
        "name": f"{sheet_name} Weight",
        "type": "line",
        "data": weight_data,
        "yAxisIndex": 0,
        "showSymbol": False,
        "smooth": True
    })
    
    series_list.append({
        "name": f"{sheet_name} DTG",
        "type": "line",
        "data": dtg_data,
        "yAxisIndex": 1,
        "showSymbol": False,
        "smooth": True,
        "lineStyle": {
            "type": "dashed"
        }
    })

option = {
    "title": {
        "text": "TGA & DTG Curves",
        "left": "center",
        "textStyle": {
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
        "data": [s["name"] for s in series_list],
        "top": 40,
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
            "formatter": "{value}"
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "min": 0,
            "max": 105
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "position": "right",
            "offset": 60
        }
    ],
    "series": series_list
}

result = {
    "figures": [
        {
            "name": "tga_combined",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
