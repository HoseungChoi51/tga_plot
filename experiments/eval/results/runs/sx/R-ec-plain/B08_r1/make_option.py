import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the 'Raw' sheet
df_raw = pd.read_excel(DATA_FILE, sheet_name='Raw')

# Extract data for plotting
temperature = df_raw['Temperature (°C)'].tolist()
weight = df_raw['Weight (%)'].tolist()

# Create TGA plot option with horizontal reference line at 50% weight and annotation
option = {
    "title": {
        "text": "TGA - Raw",
        "left": "center",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR",
            "fontSize": 16
        }
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": "{a}<br/>{b}: {c}"
    },
    "legend": {
        "data": ["Weight (%)"],
        "top": 30
    },
    "grid": {
        "left": "8%",
        "right": "8%",
        "bottom": "12%",
        "containLabel": True
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 0,
        "max": 950,
        "splitLine": {"show": True}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 40,
            "min": 0,
            "max": 110,
            "splitLine": {"show": True}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2},
            "data": [[t, w] for t, w in zip(temperature, weight)],
            "markLine": {
                "silent": True,
                "symbol": "none",
                "lineStyle": {
                    "color": "#FF6B6B",
                    "type": "dashed",
                    "width": 1.5
                },
                "label": {
                    "show": True,
                    "position": "insideEndTop",
                    "formatter": "50%",
                    "fontSize": 12,
                    "color": "#FF6B6B"
                },
                "data": [
                    {"yAxis": 50}
                ]
            }
        }
    ],
    "graphic": [
        {
            "type": "text",
            "right": 20,
            "top": 10,
            "style": {
                "text": "공기, 10 °C/min",
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 13,
                "fill": "#555555"
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
