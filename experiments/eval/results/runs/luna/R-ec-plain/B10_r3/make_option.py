import json
import re
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    matches = [c for c in df.columns if re.search(pattern, c, re.IGNORECASE)]
    if not matches:
        raise ValueError(f"Required column not found: {pattern}")
    return matches[0]

x_col = find_column(r"Temperature")
weight_col = find_column(r"Weight\s*\(%\)")
deriv_col = find_column(r"Deriv")

data = df[[x_col, weight_col, deriv_col]].apply(pd.to_numeric, errors="coerce").dropna()
x = data[x_col].tolist()
weight = data[weight_col].tolist()
deriv = data[deriv_col].tolist()

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "fontSize": 8,
        "color": "#111111"
    },
    "title": {
        "text": "Annealed",
        "left": "center",
        "top": 5,
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR, sans-serif",
            "fontSize": 8,
            "fontWeight": "normal",
            "color": "#111111"
        }
    },
    "tooltip": {"show": False},
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 24,
        "left": "center",
        "itemWidth": 12,
        "itemHeight": 8,
        "textStyle": {"fontSize": 8, "color": "#111111"}
    },
    "grid": {"left": 48, "right": 48, "top": 48, "bottom": 42},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 25,
        "min": 30,
        "max": 900,
        "axisLine": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
        "axisTick": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
        "axisLabel": {"fontSize": 8, "color": "#111111"},
        "nameTextStyle": {"fontSize": 8, "color": "#111111"},
        "splitLine": {"show": False}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 32,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
            "axisTick": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
            "axisLabel": {"fontSize": 8, "color": "#111111"},
            "nameTextStyle": {"fontSize": 8, "color": "#111111"},
            "splitLine": {"show": False}
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": -1.5,
            "max": 0.1,
            "axisLine": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
            "axisTick": {"show": True, "lineStyle": {"color": "#111111", "width": 0.8}},
            "axisLabel": {"fontSize": 8, "color": "#111111"},
            "nameTextStyle": {"fontSize": 8, "color": "#111111"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[a, b] for a, b in zip(x, weight)],
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": "#111111", "width": 1.2, "type": "solid"},
            "emphasis": {"disabled": True}
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[a, b] for a, b in zip(x, deriv)],
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": "#555555", "width": 1.0, "type": "dashed"},
            "emphasis": {"disabled": True}
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "annealed_tga",
        "option": option,
        "width": 336,
        "height": 250,
        "dpi": 600,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
