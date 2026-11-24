import pandas as pd
import json

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Annealed")

temp = df["Temperature (°C)"].dropna().tolist()
weight = df["Weight (%)"].dropna().tolist()
deriv_weight = df["Deriv. Weight (%/°C)"].dropna().tolist()

# Align lengths if needed
min_len = min(len(temp), len(weight), len(deriv_weight))
temp = temp[:min_len]
weight = weight[:min_len]
deriv_weight = deriv_weight[:min_len]

# Prepare data pairs for ECharts
weight_data = [[t, w] for t, w in zip(temp, weight)]
deriv_data = [[t, d] for t, d in zip(temp, deriv_weight)]

option = {
    "backgroundColor": "#ffffff",
    "grid": [
        {"left": 60, "right": 50, "top": 40, "bottom": 80},
        {"left": 60, "right": 50, "top": 260, "bottom": 40}
    ],
    "xAxis": [
        {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLine": {"lineStyle": {"color": "#000"}},
            "axisTick": {"show": True, "lineStyle": {"color": "#000"}},
            "splitLine": {"show": False},
            "axisLabel": {"fontSize": 8, "color": "#000"},
            "position": "top"
        },
        {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "axisLine": {"lineStyle": {"color": "#000"}},
            "axisTick": {"show": True, "lineStyle": {"color": "#000"}},
            "splitLine": {"show": False},
            "axisLabel": {"fontSize": 8, "color": "#000"},
            "position": "bottom"
        }
    ],
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 35,
            "axisLine": {"lineStyle": {"color": "#000"}},
            "axisTick": {"show": True, "lineStyle": {"color": "#000"}},
            "splitLine": {"show": False},
            "axisLabel": {"fontSize": 8, "color": "#000"},
            "min": 0,
            "max": 100
        },
        {
            "type": "value",
            "name": "DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 35,
            "axisLine": {"lineStyle": {"color": "#000"}},
            "axisTick": {"show": True, "lineStyle": {"color": "#000"}},
            "splitLine": {"show": False},
            "axisLabel": {"fontSize": 8, "color": "#000"}
        }
    ],
    "series": [
        {
            "name": "TGA",
            "type": "line",
            "data": weight_data,
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "lineStyle": {"color": "#000", "width": 1.5},
            "itemStyle": {"color": "#000"},
            "symbol": "none",
            "smooth": False
        },
        {
            "name": "DTG",
            "type": "line",
            "data": deriv_data,
            "xAxisIndex": 1,
            "yAxisIndex": 1,
            "lineStyle": {"color": "#000", "width": 1.5},
            "itemStyle": {"color": "#000"},
            "symbol": "none",
            "smooth": False
        }
    ],
    "tooltip": {"trigger": "axis"},
    "legend": {
        "show": False
    }
}

fig = {
    "name": "annealed_tga_dtg",
    "option": option,
    "width": int(3.5 * 96),
    "height": int(2.6 * 96),
    "dpi": 600,
    "formats": ["png"]
}

output = {"figures": [fig]}
print(json.dumps(output, ensure_ascii=False))
