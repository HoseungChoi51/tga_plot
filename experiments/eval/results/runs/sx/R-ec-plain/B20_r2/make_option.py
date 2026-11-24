import pandas as pd
import json

# Load the specific sheet requested by the user
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
df = pd.read_excel(file_path, sheet_name="Acid-washed")

# Extract data columns based on the preview
# x: Temperature (°C), y1: Weight (%), y2: Deriv. Weight (%/°C)
x_data = df['Temperature (°C)'].tolist()
y1_data = df['Weight (%)'].tolist()
y2_data = df['Deriv. Weight (%/°C)'].tolist()

# Prepare series data for ECharts
# Series 1: Weight (%) - Primary Y Axis
series_weight = {
    "name": "Weight (%)",
    "type": "line",
    "data": [[x, y] for x, y in zip(x_data, y1_data)],
    "showSymbol": False,
    "smooth": True,
    "lineStyle": {"width": 2},
    "itemStyle": {"color": "#5470c6"},
    "yAxisIndex": 0
}

# Series 2: Deriv. Weight (%/°C) - Secondary Y Axis
series_deriv = {
    "name": "Deriv. Weight (%/°C)",
    "type": "line",
    "data": [[x, y] for x, y in zip(x_data, y2_data)],
    "showSymbol": False,
    "smooth": True,
    "lineStyle": {"width": 2, "type": "dashed"},
    "itemStyle": {"color": "#ee6666"},
    "yAxisIndex": 1
}

# Define the ECharts option
option = {
    "title": {
        "text": "TGA Data: Acid-washed",
        "left": "center"
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": "bottom"
    },
    "grid": {
        "left": "3%",
        "right": "4%",
        "bottom": "10%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "splitLine": {
            "show": True,
            "lineStyle": {
                "type": "solid",
                "opacity": 0.3
            }
        },
        # Add minor ticks as requested
        "minorTick": {
            "show": True,
            "length": 6,
            "lineStyle": {
                "color": "#ccc",
                "width": 1
            }
        },
        "minorSplitLine": {
            "show": True,
            "lineStyle": {
                "color": "#eee",
                "width": 1
            }
        },
        "axisTick": {
            "show": True,
            "length": 8
        }
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "position": "left",
            "min": 0,
            "max": 105,
            "axisLine": {
                "lineStyle": {
                    "color": "#5470c6"
                }
            },
            "axisLabel": {
                "formatter": "{value} %"
            }
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "position": "right",
            "min": -1.5,
            "max": 0.5,
            "axisLine": {
                "lineStyle": {
                    "color": "#ee6666"
                }
            },
            "axisLabel": {
                "formatter": "{value}"
            }
        }
    ],
    "series": [series_weight, series_deriv]
}

# Construct the final JSON output
output = {
    "figures": [
        {
            "name": "tga_acid_washed",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output))
