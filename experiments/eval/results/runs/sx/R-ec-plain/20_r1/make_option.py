import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheets_data = {}
for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    # Clean column names
    df.columns = [c.strip() for c in df.columns]
    sheets_data[sheet_name] = df

# Prepare data for ECharts
# We need to create a line chart with two Y-axes (Weight and DTG)
# X-axis is Temperature
# Highlight 300-450 C range

series_list = []
legend_data = []

# Define colors for different samples
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for idx, (sheet_name, df) in enumerate(sheets_data.items()):
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    if temp_col not in df.columns or weight_col not in df.columns:
        continue
        
    x_data = df[temp_col].tolist()
    y_weight = df[weight_col].tolist()
    
    # Add Weight series
    legend_data.append(f"{sheet_name} Weight")
    series_list.append({
        "name": f"{sheet_name} Weight",
        "type": "line",
        "data": [[t, w] for t, w in zip(x_data, y_weight)],
        "yAxisIndex": 0,
        "showSymbol": False,
        "lineStyle": {"width": 2},
        "itemStyle": {"color": colors[idx % len(colors)]}
    })
    
    # Add DTG series if exists
    if dtg_col in df.columns:
        y_dtg = df[dtg_col].tolist()
        legend_data.append(f"{sheet_name} DTG")
        series_list.append({
            "name": f"{sheet_name} DTG",
            "type": "line",
            "data": [[t, d] for t, d in zip(x_data, y_dtg)],
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 1.5, "type": "dashed"},
            "itemStyle": {"color": colors[idx % len(colors)]}
        })

# Mark area for 300-450 C
mark_area_series = {
    "name": "Highlight Region",
    "type": "line",
    "data": [],
    "markArea": {
        "silent": True,
        "itemStyle": {
            "color": "rgba(200, 200, 200, 0.3)" # Light gray
        },
        "data": [
            [{"xAxis": 300}, {"xAxis": 450}]
        ]
    }
}

option = {
    "title": {
        "text": "TGA/DTG Analysis",
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
        "data": legend_data,
        "top": "8%",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
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
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "dashed"
            }
        },
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "min": 0,
            "max": 105,
            "splitLine": {
                "show": True,
                "lineStyle": {
                    "type": "dashed"
                }
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "splitLine": {
                "show": False
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "series": series_list + [mark_area_series],
    "animation": False
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
