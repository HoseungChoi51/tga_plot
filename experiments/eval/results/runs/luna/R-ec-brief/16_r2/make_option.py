import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_column(candidates):
    for col in df.columns:
        normalized = col.lower().replace(" ", "")
        if any(candidate in normalized for candidate in candidates):
            return col
    return None

x_col = find_column(["temperature", "temp", "온도"])
y_col = find_column(["weight(%)", "weight", "무게", "중량"])

if x_col is None or y_col is None:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("온도 및 무게 열을 찾지 못했습니다.")
    x_col = x_col or numeric_cols[1]
    y_col = y_col or numeric_cols[2 if len(numeric_cols) > 2 else 1]

data = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
x_values = data[x_col].astype(float).tolist()
y_values = data[y_col].astype(float).tolist()

residue_idx = int(np.argmin(np.abs(np.asarray(x_values) - 800)))
residue_temp = x_values[residue_idx]
residue_weight = y_values[residue_idx]

x_min, x_max = min(x_values), max(x_values)
y_min, y_max = min(y_values), max(y_values)
y_pad = max((y_max - y_min) * 0.08, 1.0)

option = {
    "animation": False,
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight"], "left": "center", "bottom": 8},
    "grid": {"left": 76, "right": 34, "top": 58, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 34,
        "min": x_min,
        "max": x_max,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 54,
        "min": max(0, y_min - y_pad),
        "max": y_max + y_pad,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
    },
    "series": [{
        "name": "Weight",
        "type": "line",
        "showSymbol": False,
        "smooth": False,
        "data": [[x, y] for x, y in zip(x_values, y_values)],
        "lineStyle": {"color": "#1f4e9c", "width": 2},
        "itemStyle": {"color": "#1f4e9c"},
        "markPoint": {
            "symbol": "circle",
            "symbolSize": 9,
            "data": [{
                "name": f"Residue {residue_weight:.1f}%",
                "coord": [residue_temp, residue_weight],
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "right",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "itemStyle": {"color": "#1f4e9c"}
            }]
        }
    }]
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_normal",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
