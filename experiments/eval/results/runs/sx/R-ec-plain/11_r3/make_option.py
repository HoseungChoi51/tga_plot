import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def read_sheet(file_path, sheet_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
    # Ensure column names are stripped and match expected keys from preview
    cols = df.columns.tolist()
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for c in cols:
        if 'Temperature' in str(c):
            temp_col = c
        elif 'Weight' in str(c):
            weight_col = c
        elif 'D.W' in str(c) or 'DTG' in str(c):
            dtg_col = c
            
    if not all([temp_col, weight_col, dtg_col]):
        return None
        
    data = df[[temp_col, weight_col, dtg_col]].dropna().values.tolist()
    return {
        "temperature": [row[0] for row in data],
        "weight": [row[1] for row in data],
        "dtg": [row[2] for row in data]
    }

sheets_info = [
    {"name": "1006R1-V normal", "label": "Normal"},
    {"name": "1006R1-V acid", "label": "Acid"},
    {"name": "1006R1-V 750C", "label": "750C"}
]

series_weight = []
series_dtg = []

for s in sheets_info:
    data = read_sheet(DATA_FILE, s["name"])
    if data:
        # Weight series (Left Y axis)
        series_weight.append({
            "name": f"{s['label']} Weight",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(data["temperature"], data["weight"])],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2}
        })
        
        # DTG series (Right Y axis) - dashed line to distinguish
        series_dtg.append({
            "name": f"{s['label']} DTG",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(data["temperature"], data["dtg"])],
            "smooth": True,
            "symbol": "none",
            "lineStyle": {"width": 2, "type": "dashed"}
        })

option = {
    "title": {
        "text": "TGA / DTG Analysis",
        "left": "center",
        "top": 10
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": [f"{s['label']} Weight" for s in sheets_info] + [f"{s['label']} DTG" for s in sheets_info],
        "bottom": 30
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "type": "value",
        "min": 30,
        "max": 900,
        "axisLine": {"onZero": False},
        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "axisLine": {"onZero": False},
            "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "axisLine": {"onZero": False},
            "splitLine": {"show": False}
        }
    ],
    "series": series_weight + series_dtg
}

output = {
    "figures": [
        {
            "name": "tga_plot",
            "option": option,
            "width": 800,
            "height": 600,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
