import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(c).strip() for c in df.columns]

x_col = next(c for c in df.columns if "Temperature" in c)
y_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

data = []
for x, y in zip(df[x_col], df[y_col]):
    if pd.notna(x) and pd.notna(y):
        data.append([float(x), float(y)])

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "title": {
        "text": "Raw",
        "left": "center",
        "top": 10,
        "textStyle": {"fontSize": 16, "fontWeight": "normal"}
    },
    "grid": {"left": 76, "right": 42, "top": 64, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 48,
        "min": 0,
        "max": 105,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
    },
    "series": [{
        "name": "Weight (%)",
        "type": "line",
        "data": data,
        "showSymbol": False,
        "lineStyle": {"color": "#276FBF", "width": 2},
        "markLine": {
            "symbol": ["none", "none"],
            "silent": True,
            "lineStyle": {"color": "#D9534F", "width": 1.5, "type": "dashed"},
            "label": {
                "show": True,
                "formatter": "50%",
                "position": "insideEndTop",
                "color": "#D9534F"
            },
            "data": [{"yAxis": 50}]
        }
    }],
    "graphic": [{
        "type": "text",
        "right": 20,
        "top": 18,
        "style": {
            "text": "공기, 10 °C/min",
            "font": "14px Noto Sans CJK KR",
            "fill": "#333333",
            "textAlign": "right"
        }
    }],
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    }
}

print(json.dumps({
    "figures": [{
        "name": "raw_tga",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
