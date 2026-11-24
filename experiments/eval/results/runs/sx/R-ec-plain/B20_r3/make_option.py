import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

# Read the Acid-washed sheet
df = pd.read_excel(DATA_FILE, sheet_name="Acid-washed", header=0)

# Extract data
temperature = df["Temperature (°C)"].tolist()
weight = df["Weight (%)"].tolist()
deriv_weight = df["Deriv. Weight (%/°C)"].tolist()

# Build ECharts option
option = {
    "title": {
        "text": "TGA - Acid-washed",
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
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 30,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR"
        }
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "12%",
        "containLabel": True
    },
    "xAxis": [
        {
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "type": "value",
            "min": 30,
            "max": 900,
            "splitLine": {"show": False},
            "axisTick": {
                "show": True,
                "alignWithLabel": True
            },
            "minorTick": {
                "show": True,
                "length": 4
            },
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR"
            }
        }
    ],
    "yAxis": [
        {
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "type": "value",
            "position": "left",
            "axisLabel": {
                "formatter": "{value} %",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {"show": True, "lineStyle": {"type": "dashed"}}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 50,
            "type": "value",
            "position": "right",
            "axisLabel": {
                "formatter": "{value}",
                "fontFamily": "Noto Sans CJK KR"
            },
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[t, w] for t, w in zip(temperature, weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#5470c6"},
            "itemStyle": {"color": "#5470c6"}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[t, d] for t, d in zip(temperature, deriv_weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#ee6666"},
            "itemStyle": {"color": "#ee6666"}
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
