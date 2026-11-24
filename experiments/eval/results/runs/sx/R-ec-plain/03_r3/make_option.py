import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V acid")

# Extract columns
temp = df["Temperature"].tolist()
weight = df["Weight(%)"].tolist()
dw = df["D.W(%/C)"].tolist()

# Filter data for x-axis range 100~800
mask = (df["Temperature"] >= 100) & (df["Temperature"] <= 800)
filtered_df = df[mask]

temp_filtered = filtered_df["Temperature"].tolist()
weight_filtered = filtered_df["Weight(%)"].tolist()
dw_filtered = filtered_df["D.W(%/C)"].tolist()

# Find peaks in D.W(%/C) - looking for local minima (since weight loss is negative derivative)
# We'll use a simple approach: find the two most significant drops
import numpy as np

dw_arr = np.array(dw_filtered)
temp_arr = np.array(temp_filtered)

# Find indices of local minima in DW (most negative values indicate maximum rate of weight loss)
# Sort by DW value and pick top 2 most negative
sorted_indices = np.argsort(dw_arr)[:2]  # Two smallest (most negative) values

peak_temps = [float(temp_arr[i]) for i in sorted_indices]
peak_dws = [float(dw_arr[i]) for i in sorted_indices]

# Create ECharts option
option = {
    "title": {
        "text": "TGA/DTA Curve - 1006R1-V acid",
        "left": "center",
        "top": 10,
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
        "data": ["Weight (%)", "D.W (%/°C)"],
        "top": 35,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "12%",
        "top": "18%"
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "type": "value",
        "min": 100,
        "max": 800,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "axisLabel": {
            "formatter": "{value}"
        }
    },
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "axisLine": {
                "show": True,
                "lineStyle": {
                    "color": "#5470c6"
                }
            },
            "axisTick": {
                "show": True,
                "lineStyle": {
                    "color": "#5470c6"
                }
            },
            "axisLabel": {
                "color": "#5470c6"
            }
        },
        {
            "name": "D.W (%/°C)",
            "type": "value",
            "position": "right",
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR"
            },
            "axisLine": {
                "show": True,
                "lineStyle": {
                    "color": "#ee6666"
                }
            },
            "axisTick": {
                "show": True,
                "lineStyle": {
                    "color": "#ee6666"
                }
            },
            "axisLabel": {
                "color": "#ee6666"
            }
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "lineStyle": {
                "width": 2,
                "color": "#5470c6"
            },
            "itemStyle": {
                "color": "#5470c6"
            },
            "data": [[t, w] for t, w in zip(temp_filtered, weight_filtered)]
        },
        {
            "name": "D.W (%/°C)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "yAxisIndex": 1,
            "lineStyle": {
                "width": 2,
                "color": "#ee6666"
            },
            "itemStyle": {
                "color": "#ee6666"
            },
            "data": [[t, d] for t, d in zip(temp_filtered, dw_filtered)],
            "markPoint": {
                "data": [
                    {
                        "coord": [peak_temps[0], peak_dws[0]],
                        "name": f"Peak 1\n{peak_temps[0]:.1f}°C",
                        "itemStyle": {"color": "#ee6666"},
                        "label": {
                            "show": True,
                            "formatter": f"{peak_temps[0]:.1f}°C",
                            "position": "top",
                            "fontSize": 10,
                            "fontFamily": "Noto Sans CJK KR"
                        }
                    },
                    {
                        "coord": [peak_temps[1], peak_dws[1]],
                        "name": f"Peak 2\n{peak_temps[1]:.1f}°C",
                        "itemStyle": {"color": "#ee6666"},
                        "label": {
                            "show": True,
                            "formatter": f"{peak_temps[1]:.1f}°C",
                            "position": "top",
                            "fontSize": 10,
                            "fontFamily": "Noto Sans CJK KR"
                        }
                    }
                ]
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

print(json.dumps(result))
