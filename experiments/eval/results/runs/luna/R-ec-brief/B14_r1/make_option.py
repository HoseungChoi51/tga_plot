import json
import math
import os

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
SHEET_NAME = "PVC"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_column(keywords):
    for col in df.columns:
        name = col.lower()
        if any(word in name for word in keywords):
            return col
    return None

x_col = find_column(["temperature", "temp"])
weight_col = find_column(["weight"])
dtg_col = find_column(["deriv", "dtg"])

if x_col is None or weight_col is None or dtg_col is None:
    raise ValueError("PVC 시트에서 온도, 무게, DTG 열을 찾을 수 없습니다.")

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(x_col)

temperature = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

residue_idx = int(np.argmin(np.abs(temperature - 800.0)))
residue_x = float(temperature[residue_idx])
residue_y = float(weight[residue_idx])

peak_mask = temperature > 150.0
if peak_mask.any():
    eligible = np.flatnonzero(peak_mask)
    peak_idx = int(eligible[np.argmax(-dtg[peak_mask])])
    peak_x = float(temperature[peak_idx])
    peak_y = float(-dtg[peak_idx])
else:
    peak_x = peak_y = None

weight_series = {
    "name": "Weight (%)",
    "type": "line",
    "showSymbol": False,
    "yAxisIndex": 0,
    "lineStyle": {"color": "#1f4e9c", "width": 3},
    "itemStyle": {"color": "#1f4e9c"},
    "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
    "markPoint": {
        "symbol": "circle",
        "symbolSize": 13,
        "itemStyle": {"color": "#1f4e9c", "borderColor": "#ffffff", "borderWidth": 2},
        "label": {
            "show": True,
            "formatter": f"Residue {residue_y:.1f}%",
            "position": "right",
            "fontSize": 16,
            "color": "#1f4e9c",
            "backgroundColor": "#ffffff",
            "padding": [4, 6],
        },
        "data": [{"coord": [residue_x, residue_y]}],
    },
}

dtg_series = {
    "name": "−DTG (%/°C)",
    "type": "line",
    "showSymbol": False,
    "yAxisIndex": 1,
    "lineStyle": {"color": "#c0392b", "width": 3},
    "itemStyle": {"color": "#c0392b"},
    "data": [[float(x), float(-y)] for x, y in zip(temperature, dtg)],
}

if peak_x is not None:
    dtg_series["markPoint"] = {
        "symbol": "circle",
        "symbolSize": 13,
        "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 2},
        "label": {
            "show": True,
            "formatter": f"{peak_x:.0f} °C",
            "position": "top",
            "fontSize": 16,
            "color": "#c0392b",
            "backgroundColor": "#ffffff",
            "padding": [4, 6],
        },
        "data": [{"coord": [peak_x, peak_y]}],
    }

option = {
    "animation": False,
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "top": 18,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 22, "fontWeight": "bold", "color": "#222222"},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight (%)", "−DTG (%/°C)"],
        "left": "center",
        "top": 55,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "grid": {"left": 95, "right": 95, "top": 110, "bottom": 80, "containLabel": True},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisTick": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "−DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisTick": {"show": True},
            "splitLine": {"show": False},
        },
    ],
    "series": [weight_series, dtg_series],
}

print(json.dumps({
    "figures": [{
        "name": "PVC",
        "option": option,
        "width": 960,
        "height": 576,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
