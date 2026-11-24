import pandas as pd
import numpy as np
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Read the second sheet (PVC)
df = pd.read_excel(DATA_FILE, sheet_name=1)

# Extract columns
temp = df["Temperature (°C)"].values
weight = df["Weight (%)"].values

# Find weight at 300°C and 600°C by interpolation
w_300 = np.interp(300, temp, weight)
w_600 = np.interp(600, temp, weight)

# Prepare data for ECharts - use line chart with temperature on x-axis
# Sample data to reduce points but keep key regions
n = len(temp)
step = max(1, n // 500)
sampled_temp = temp[::step].tolist()
sampled_weight = weight[::step].tolist()

# Ensure last point is included
if sampled_temp[-1] != temp[-1]:
    sampled_temp.append(float(temp[-1]))
    sampled_weight.append(float(weight[-1]))

# Build series data as [x, y] pairs
series_data = [[float(t), float(w)] for t, w in zip(sampled_temp, sampled_weight)]

# Mark points at 300 and 600
mark_points = [
    {"coord": [300.0, float(w_300)], "name": f"300°C: {w_300:.2f}%"},
    {"coord": [600.0, float(w_600)], "name": f"600°C: {w_600:.2f}%"}
]

option = {
    "title": {
        "text": "PVC TGA 곡선",
        "subtext": f"300°C 무게: {w_300:.2f}%, 600°C 무게: {w_600:.2f}%",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        "subtextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12}
    },
    "tooltip": {
        "trigger": "axis",
        "formatter": None,
        "axisPointer": {"type": "cross"}
    },
    "grid": {
        "left": "8%",
        "right": "5%",
        "bottom": "12%",
        "top": "18%"
    },
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 30,
        "min": 0,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": {
        "type": "value",
        "name": "무게 (%)",
        "nameLocation": "middle",
        "nameGap": 40,
        "min": 0,
        "max": 105,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "series": [
        {
            "name": "PVC Weight",
            "type": "line",
            "smooth": True,
            "showSymbol": False,
            "data": series_data,
            "lineStyle": {"width": 2, "color": "#e74c3c"},
            "itemStyle": {"color": "#e74c3c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 10,
                "itemStyle": {"color": "#e74c3c", "borderColor": "#fff", "borderWidth": 2},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": "{b}",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                    "color": "#333"
                },
                "data": mark_points
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
