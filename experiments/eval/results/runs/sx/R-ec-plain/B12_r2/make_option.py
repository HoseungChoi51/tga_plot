import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

# Read the CSV file
df = pd.read_csv(DATA_FILE)

# Extract Temperature and Weight columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values

# Filter data for x range 100 to 900
mask = (temp >= 100) & (temp <= 900)
filtered_temp = temp[mask]
filtered_weight = weight[mask]

# Find residue at 900 °C (last point in filtered data or closest to 900)
idx_900 = np.argmin(np.abs(temp - 900))
residue_900 = weight[idx_900]

# Build ECharts option
option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "TGA Weight Curve",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontSize": 16,
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{b}<br/>Temperature: {a0} °C<br/>Weight: {c0} %"
    },
    "grid": {
        "left": 70,
        "right": 40,
        "bottom": 50,
        "top": 60
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 100,
        "max": 900,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "splitLine": {
            "show": True,
            "lineStyle": {
                "color": "#e0e0e0"
            }
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 45,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
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
            "name": "Weight",
            "type": "line",
            "data": [[float(t), float(w)] for t, w in zip(filtered_temp, filtered_weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#1f77b4"
            },
            "markPoint": {
                "data": [
                    {
                        "coord": [900.0, float(residue_900)],
                        "label": {
                            "show": True,
                            "formatter": f"Residue @900°C\n{residue_900:.2f}%",
                            "position": "top",
                            "fontSize": 12,
                            "fontFamily": "Noto Sans CJK KR",
                            "color": "#d62728"
                        },
                        "itemStyle": {
                            "color": "#d62728"
                        },
                        "symbolSize": 8
                    }
                ]
            }
        }
    ]
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
