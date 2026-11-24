import json
import re
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    for column in df.columns:
        if re.search(pattern, column, flags=re.IGNORECASE):
            return column
    raise ValueError(f"Could not find a column matching {pattern!r}")

x_col = find_column(r"Temperature")
weight_col = find_column(r"Weight\s*\(%\)")
deriv_col = find_column(r"Deriv")

data = []
for _, row in df.iterrows():
    x = pd.to_numeric(row[x_col], errors="coerce")
    weight = pd.to_numeric(row[weight_col], errors="coerce")
    deriv = pd.to_numeric(row[deriv_col], errors="coerce")
    if pd.notna(x) and pd.notna(weight) and pd.notna(deriv):
        data.append([float(x), float(weight), float(deriv)])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "fontSize": 8,
        "color": "#000000",
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
        "top": 4,
        "textStyle": {"fontSize": 8, "color": "#000000"},
        "itemWidth": 12,
        "itemHeight": 8,
    },
    "grid": {"left": 48, "right": 48, "top": 30, "bottom": 42},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 27,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#000000", "width": 1}},
        "axisTick": {"lineStyle": {"color": "#000000"}},
        "axisLabel": {"fontSize": 8, "color": "#000000"},
        "nameTextStyle": {"fontSize": 8, "color": "#000000"},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#000000", "width": 1}},
            "axisTick": {"lineStyle": {"color": "#000000"}},
            "axisLabel": {"fontSize": 8, "color": "#000000"},
            "nameTextStyle": {"fontSize": 8, "color": "#000000"},
            "splitLine": {"show": False},
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": -1.5,
            "max": 0.2,
            "axisLine": {"show": True, "lineStyle": {"color": "#000000", "width": 1}},
            "axisTick": {"lineStyle": {"color": "#000000"}},
            "axisLabel": {"fontSize": 8, "color": "#000000"},
            "nameTextStyle": {"fontSize": 8, "color": "#000000"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "data": [[row[0], row[1]] for row in data],
            "showSymbol": False,
            "lineStyle": {"color": "#000000", "width": 1.2, "type": "solid"},
            "itemStyle": {"color": "#000000"},
        },
        {
            "name": "Deriv. Weight (%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[row[0], row[2]] for row in data],
            "showSymbol": False,
            "lineStyle": {"color": "#000000", "width": 1.0, "type": "dashed"},
            "itemStyle": {"color": "#000000"},
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "annealed_tga",
        "option": option,
        "width": 336,
        "height": 250,
        "dpi": 600,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
