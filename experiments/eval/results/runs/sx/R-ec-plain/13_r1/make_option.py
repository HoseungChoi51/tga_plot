import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"

# Read the Excel file, sheet 'CNT-01'
df = pd.read_excel(DATA_FILE, sheet_name='CNT-01', header=0)

# Extract relevant columns: Temperature (°C) and Weight (mg)
x_data = df['Temperature (°C)'].tolist()
y_data = df['Weight (mg)'].tolist()

# Prepare ECharts option
option = {
    "title": {
        "text": "TGA - Weight vs Temperature",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a} <br/>{b}: {c}"
    },
    "grid": {
        "left": "10%",
        "right": "5%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (mg)",
        "nameLocation": "middle",
        "nameGap": 40,
        "axisLabel": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_data)],
            "smooth": False,
            "showSymbol": False,
            "lineStyle": {
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

print(json.dumps(result))
