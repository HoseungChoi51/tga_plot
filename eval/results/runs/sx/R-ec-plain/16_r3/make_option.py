import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal", header=0)

# Extract data
temperature = df["Temperature"].tolist()
weight = df["Weight(%)"].tolist()

# Prepare ECharts option
option = {
    "title": {
        "text": "TGA - 1006R1-V normal",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}<br/>온도: {b} °C<br/>무게: {c} %"
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "top": "15%",
        "bottom": "12%"
    },
    "xAxis": {
        "name": "Temperature (°C)",
        "type": "value",
        "nameLocation": "middle",
        "nameGap": 30,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "name": "Weight (%)",
        "type": "value",
        "nameLocation": "middle",
        "nameGap": 40,
        "nameTextStyle": {
            "fontFamily": "Noto Sans CJK KR"
        },
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "data": [[t, w] for t, w in zip(temperature, weight)],
            "lineStyle": {
                "width": 2,
                "color": "#1f77b4"
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
