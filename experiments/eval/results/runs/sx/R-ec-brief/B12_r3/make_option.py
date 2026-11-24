import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

# Read data
df = pd.read_csv(DATA_FILE)

# Column names from preview
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"

# Filter x range 100 to 900
mask = (df[temp_col] >= 100) & (df[temp_col] <= 900)
filtered_df = df[mask].copy()

# Prepare data for ECharts: [temperature, weight] pairs
data_points = filtered_df[[temp_col, weight_col]].dropna().values.tolist()

# Find residue at nearest point to 900 °C
# We need the original full data to find the closest to 900°C
full_df = df.dropna(subset=[temp_col, weight_col])
idx_900 = (full_df[temp_col] - 900).abs().idxmin()
residue_temp = full_df.loc[idx_900, temp_col]
residue_weight = full_df.loc[idx_900, weight_col]

# Build ECharts option
option = {
    "title": {
        "text": "caox",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "top": "15%",
        "bottom": "12%"
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "type": "value",
        "min": 100,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "color": "#e0e0e0"
            }
        }
    },
    "yAxis": {
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "type": "value",
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 12
        },
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "color": "#e0e0e0"
            }
        }
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": data_points,
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "color": "#1f4e9c",
                "width": 2
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [residue_temp, residue_weight],
                        "symbol": "circle",
                        "symbolSize": 8,
                        "itemStyle": {
                            "color": "#1f4e9c"
                        },
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_weight:.1f}%",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12,
                            "color": "#1f4e9c"
                        }
                    }
                ]
            }
        }
    ],
    "legend": {
        "show": False
    }
}

output = {
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

print(json.dumps(output, ensure_ascii=False))
