import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)

series_weight = []
series_dtg = []

colors_weight = ["#1f77b4", "#ff7f0e", "#2ca02c"]
colors_dtg = ["#aec7e8", "#ffbb78", "#98df8a"]

for idx, sheet_name in enumerate(xls.sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Extract data
    temp = df["Temperature"].values
    weight = df["Weight(%)"].values
    dtg = df["D.W(%/C)"].values
    
    # Create line series for Weight (%) - left y-axis
    series_weight.append({
        "name": f"{sheet_name} Weight(%)",
        "type": "line",
        "data": [[float(t), float(w)] for t, w in zip(temp, weight)],
        "yAxisIndex": 0,
        "showSymbol": False,
        "lineStyle": {
            "width": 2,
            "color": colors_weight[idx % len(colors_weight)]
        },
        "itemStyle": {
            "color": colors_weight[idx % len(colors_weight)]
        }
    })
    
    # Create line series for D.W (%/C) - right y-axis
    series_dtg.append({
        "name": f"{sheet_name} D.W(%/C)",
        "type": "line",
        "data": [[float(t), float(d)] for t, d in zip(temp, dtg)],
        "yAxisIndex": 1,
        "showSymbol": False,
        "lineStyle": {
            "width": 1.5,
            "color": colors_dtg[idx % len(colors_dtg)],
            "type": "dashed"
        },
        "itemStyle": {
            "color": colors_dtg[idx % len(colors_dtg)]
        }
    })

all_series = series_weight + series_dtg

option = {
    "title": {
        "text": "TGA Analysis: Weight Loss and Derivative",
        "left": "center",
        "textStyle": {
            "fontSize": 16,
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        },
        "formatter": None
    },
    "legend": {
        "data": [s["name"] for s in all_series],
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": 60,
        "right": 60,
        "bottom": 60,
        "top": 80,
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 35,
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
            "max": 105,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "lineStyle": {
                    "type": "dashed"
                }
            }
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "position": "right",
            "min": -1.1,
            "max": 0.01,
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": all_series
}

output = {
    "figures": [
        {
            "name": "tga_combined",
            "option": option,
            "width": 800,
            "height": 500,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
