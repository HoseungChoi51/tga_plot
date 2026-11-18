import pandas as pd
import json
import numpy as np

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)

sheets_data = {}
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    # Ensure column names are stripped
    df.columns = [str(c).strip() for c in df.columns]
    sheets_data[sheet_name] = df

# Define colors for each sample
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green

series_list = []
legend_names = []

for idx, (sheet_name, df) in enumerate(sheets_data.items()):
    temp = df['Temperature'].values
    weight = df['Weight(%)'].values
    
    # Find index closest to 700°C for residual weight calculation
    if len(temp) > 0:
        idx_700 = np.argmin(np.abs(temp - 700))
        res_weight = round(weight[idx_700], 2)
        
        # Create label with residual weight at 700C
        label = f"{sheet_name} (Res. @700°C: {res_weight}%)"
        legend_names.append(label)
        
        # Prepare data for TGA curve (Temperature vs Weight)
        tga_data = [[float(t), float(w)] for t, w in zip(temp, weight)]
        
        series_list.append({
            "name": label,
            "type": "line",
            "showSymbol": False,
            "data": tga_data,
            "lineStyle": {"width": 2},
            "itemStyle": {"color": colors[idx % len(colors)]},
            "yAxisIndex": 0
        })

# Build ECharts option
option = {
    "title": {
        "text": "TGA Analysis Results",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None,  # Default formatter works fine
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": legend_names,
        "bottom": 5,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        }
    },
    "grid": {
        "left": "8%",
        "right": "5%",
        "top": "15%",
        "bottom": "15%"
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "min": 30,
        "max": 900,
        "axisLabel": {
            "formatter": "{value}"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed"
            }
        }
    },
    "yAxis": {
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "type": "value",
        "min": 0,
        "max": 105,
        "axisLabel": {
            "formatter": "{value}"
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
            "name": "tga_plot",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result, ensure_ascii=False))
