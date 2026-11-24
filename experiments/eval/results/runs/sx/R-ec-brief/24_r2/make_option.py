import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

# Read the Excel file
df = pd.read_excel(DATA_FILE, sheet_name="CNT-01", header=0)

# Extract columns based on the preview
temp_col = "Temperature (°C)"
weight_pct_col = "Weight (%)"
heat_flow_col = "Heat Flow (W/g)"

# Get data
temperature = df[temp_col].values.astype(float)
weight_pct = df[weight_pct_col].values.astype(float)
heat_flow = df[heat_flow_col].values.astype(float)

# Find residue at 800°C (nearest measured point)
idx_800 = np.argmin(np.abs(temperature - 800))
residue_weight = weight_pct[idx_800]
residue_temp = temperature[idx_800]

# Prepare series data for ECharts
# Series 1: Weight (%) on y1 (left axis)
series_weight = []
for t, w in zip(temperature, weight_pct):
    if not (np.isnan(t) or np.isnan(w)):
        series_weight.append([float(t), float(w)])

# Series 2: Heat Flow on y2 (right axis)
series_heat_flow = []
for t, hf in zip(temperature, heat_flow):
    if not (np.isnan(t) or np.isnan(hf)):
        series_heat_flow.append([float(t), float(hf)])

# Build the option
option = {
    "title": {
        "text": "CNT-01",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Heat flow (W/g)"],
        "orient": "vertical",
        "left": "left",
        "top": "middle",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "type": "value",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "lineStyle": {
                    "color": "#ddd"
                }
            }
        },
        {
            "name": "Heat flow (W/g)",
            "type": "value",
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 10
            },
            "splitLine": {
                "show": False
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": series_weight,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [float(residue_temp), float(residue_weight)],
                        "symbol": "circle",
                        "symbolSize": 8,
                        "itemStyle": {
                            "color": "#1f4e9c"
                        },
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_weight:.1f}%",
                            "position": "top",
                            "distance": 10,
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 11,
                            "color": "#1f4e9c"
                        }
                    }
                ]
            }
        },
        {
            "name": "Heat flow (W/g)",
            "type": "line",
            "yAxisIndex": 1,
            "data": series_heat_flow,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#c0392b",
                "width": 2
            }
        }
    ]
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
