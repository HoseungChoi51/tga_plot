import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet requested
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal", header=0)

# Extract data columns based on preview info
# Temperature (X), Weight(%) (Y1), D.W(%/C) (Y2)
temp = df['Temperature'].tolist()
weight = df['Weight(%)'].tolist()
d_weight = df['D.W(%/C)'].tolist()

# Prepare series data for ECharts
series_data_tg = [[t, w] for t, w in zip(temp, weight)]
series_data_dtg = [[t, dw] for t, dw in zip(temp, d_weight)]

option = {
    "title": {
        "text": "CNT 산화 거동",
        "left": "center",
        "top": 10,
        "textStyle": {
            "fontSize": 18,
            "color": "#00008B"  # Navy Blue (남색)
        }
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {
            "type": "cross"
        }
    },
    "legend": {
        "data": ["Weight (%)", "DTG (%/°C)"],
        "top": 40,
        "right": 10
    },
    "grid": {
        "left": "3%",
        "right": "4%",
        "bottom": "3%",
        "containLabel": True
    },
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "type": "value",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 30,
            "max": 900
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "type": "value",
            "position": "left",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": 0,
            "max": 110
        },
        {
            "name": "DTG (%/°C)",
            "type": "value",
            "position": "right",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": -1.1,
            "max": 0.1
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "showSymbol": False,
            "smooth": True,
            "data": series_data_tg,
            "itemStyle": {
                "color": "#5470C6"
            },
            "lineStyle": {
                "width": 2
            }
        },
        {
            "name": "DTG (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": True,
            "data": series_data_dtg,
            "itemStyle": {
                "color": "#EE6666"
            },
            "lineStyle": {
                "width": 2
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
