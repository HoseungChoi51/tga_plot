import pandas as pd
import numpy as np
import json

# Load data
file_path = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
df = pd.read_csv(file_path)

# Extract columns based on the preview info
# Time (min), Temperature (°C), Weight (%), Deriv. Weight (%/°C), Heat Flow (W/g)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

# Clean data: remove NaN and ensure numeric types
df_clean = df[[temp_col, weight_col, dtg_col]].dropna()
df_clean[temp_col] = pd.to_numeric(df_clean[temp_col], errors='coerce')
df_clean[weight_col] = pd.to_numeric(df_clean[weight_col], errors='coerce')
df_clean[dtg_col] = pd.to_numeric(df_clean[dtg_col], errors='coerce')
df_clean.dropna(inplace=True)

x_data = df_clean[temp_col].tolist()
y_weight = df_clean[weight_col].tolist()
y_dtg = df_clean[dtg_col].tolist()

# Define ECharts options for two separate charts sharing the same X-axis conceptually, 
# but rendered as two distinct figures in the JSON output as requested ("따로 나눠서").
# The user asked to split them into top and bottom graphs. Since we output a list of figures,
# we will create two entries in the "figures" array.

common_x_axis = {
    "name": "온도 (°C)",
    "type": "value",
    "axisLabel": {"formatter": "{value}"},
    "splitLine": {"show": True, "lineStyle": {"color": "#eee"}},
    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12}
}

# Figure 1: TGA (Weight %)
option_tga = {
    "title": {
        "text": "TGA (중량 변화)",
        "left": "center",
        "top": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 14}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "backgroundColor": "rgba(50,50,50,0.8)",
        "borderColor": "#777",
        "textStyle": {"color": "#fff", "fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": common_x_axis,
    "yAxis": {
        "name": "무게 (%)",
        "type": "value",
        "scale": True,
        "axisLabel": {"formatter": "{value}%"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12}
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_weight)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#5470c6"}
        }
    ]
}

# Figure 2: DTG (Derivative Weight)
option_dtg = {
    "title": {
        "text": "DTG (미분 중량 변화)",
        "left": "center",
        "top": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 14}
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "backgroundColor": "rgba(50,50,50,0.8)",
        "borderColor": "#777",
        "textStyle": {"color": "#fff", "fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {
        "left": "10%",
        "right": "10%",
        "bottom": "15%",
        "containLabel": True
    },
    "xAxis": common_x_axis,
    "yAxis": {
        "name": "DTG (%/°C)",
        "type": "value",
        "scale": True,
        "axisLabel": {"formatter": "{value}"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12}
    },
    "series": [
        {
            "name": "DTG",
            "type": "line",
            "data": [[x, y] for x, y in zip(x_data, y_dtg)],
            "smooth": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#91cc75"},
            "areaStyle": {"opacity": 0.3, "color": "#91cc75"}
        }
    ]
}

output = {
    "figures": [
        {
            "name": "tga_weight",
            "option": option_tga,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        },
        {
            "name": "dtg_derivative",
            "option": option_dtg,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(output, ensure_ascii=False))
