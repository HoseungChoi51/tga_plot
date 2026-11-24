import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)

series_list = []
legend_data = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]
    
    # Identify columns based on preview info
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns or dtg_col not in df.columns:
        continue
        
    # Extract data and round to reduce JSON size
    temps = df[temp_col].round(2).tolist()
    weights = df[weight_col].round(4).tolist()
    dtgs = df[dtg_col].round(6).tolist()
    
    # Create TGA series (left Y axis)
    tga_series_name = f"{sheet_name} - Weight"
    legend_data.append(tga_series_name)
    series_list.append({
        "name": tga_series_name,
        "type": "line",
        "yAxisIndex": 0,
        "data": [[t, w] for t, w in zip(temps, weights)],
        "showSymbol": False,
        "lineStyle": {"width": 1.5},
        "smooth": False
    })
    
    # Create DTG series (right Y axis)
    dtg_series_name = f"{sheet_name} - dW/dT"
    legend_data.append(dtg_series_name)
    series_list.append({
        "name": dtg_series_name,
        "type": "line",
        "yAxisIndex": 1,
        "data": [[t, d] for t, d in zip(temps, dtgs)],
        "showSymbol": False,
        "lineStyle": {"width": 1.5, "type": "dashed"},
        "smooth": False
    })

# Build ECharts option
option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA / DTG Analysis",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "formatter": None  # Will be handled by default or simple string if needed, but keeping it simple for JSON
    },
    "legend": {
        "data": legend_data,
        "top": 40,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 10
        }
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "12%",
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
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "min": 0,
            "max": 100,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        {
            "type": "value",
            "name": "dW/dT (%/°C)",
            "position": "right",
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "series": series_list
}

# Dimensions: 8 inches x 5 inches at 96 dpi -> 768 x 480 px
width_px = int(8 * 96)
height_px = int(5 * 96)

result = {
    "figures": [
        {
            "name": "tga_dtg_plot",
            "option": option,
            "width": width_px,
            "height": height_px,
            "dpi": 600,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result))
