import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

# Read the CSV file
df = pd.read_csv(DATA_FILE)

# Extract relevant columns
temp = df["Temperature (°C)"].values
weight = df["Weight (%)"].values

# Filter data for x range 100 to 900
mask = (temp >= 100) & (temp <= 900)
filtered_temp = temp[mask]
filtered_weight = weight[mask]

# Find residue at nearest point to 900 °C
idx_900 = np.argmin(np.abs(temp - 900))
residue_temp = temp[idx_900]
residue_weight = weight[idx_900]

# Prepare series data for ECharts
series_data = [[float(t), float(w)] for t, w in zip(filtered_temp, filtered_weight)]

# Build the ECharts option
option = {
    "title": {
        "text": "caox",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 14
        }
    },
    "grid": {
        "left": 60,
        "right": 30,
        "top": 50,
        "bottom": 50
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 100,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        },
        "axisLine": {"show": True},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 11
        },
        "axisLine": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#eee"}}
    },
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "data": series_data,
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
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 11,
                            "color": "#1f4e9c"
                        }
                    }
                ]
            }
        }
    ],
    "tooltip": {
        "trigger": "axis",
        "formatter": None
    }
}

# Remove tooltip formatter since we can't use JS functions
del option["tooltip"]["formatter"]

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
