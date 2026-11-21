import json
import os
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    return re.sub(r"[^\w.-]+", "_", str(value).strip()).strip("_") or "plot"

def find_column(columns, pattern, fallback):
    for col in columns:
        if re.search(pattern, str(col), re.I):
            return col
    return columns[fallback]

def number(value):
    return float(value) if pd.notna(value) and np.isfinite(value) else None

book = pd.ExcelFile(DATA_FILE)
figures = []

for sheet_name in book.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df = df.dropna(how="all")
    if df.empty or len(df.columns) < 3:
        continue

    cols = list(df.columns)
    xcol = find_column(cols, r"temp", 1 if len(cols) > 1 else 0)
    y1col = find_column(cols, r"weight", 2 if len(cols) > 2 else 1)
    y2col = find_column(cols, r"(d\.?\s*w|dtg|derivative)", 3 if len(cols) > 3 else len(cols) - 1)

    x = pd.to_numeric(df[xcol], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(df[y1col], errors="coerce").to_numpy(dtype=float)
    dtg = pd.to_numeric(df[y2col], errors="coerce").to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]

    residue_target = 700.0
    residue_idx = int(np.argmin(np.abs(x - residue_target)))
    residue_x = float(x[residue_idx])
    residue_y = float(weight[residue_idx])

    peak_mask = x > 150
    if np.any(peak_mask):
        peak_indices = np.flatnonzero(peak_mask)
        # DTG mass-loss values are negative; invert so the loss peak points upward.
        peak_idx = int(peak_indices[np.argmax(-dtg[peak_mask])])
        peak_x = float(x[peak_idx])
        peak_y = float(-dtg[peak_idx])
    else:
        peak_x, peak_y = None, None

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight (%)", "-DTG (%/°C)"], "left": "center"},
        "grid": {"left": 75, "right": 75, "top": 75, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 55,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 55,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "data": [[number(a), number(b)] for a, b in zip(x, weight)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": "Residue {:.2f}%".format(residue_y),
                        "position": "right",
                        "color": "#1f4e9c",
                        "fontFamily": "Noto Sans CJK KR"
                    },
                    "data": [{"coord": [residue_x, residue_y]}]
                }
            },
            {
                "name": "-DTG (%/°C)",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "data": [[number(a), number(-b)] for a, b in zip(x, dtg)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": "{:.0f} °C".format(peak_x) if peak_x is not None else "",
                        "position": "top",
                        "color": "#c0392b",
                        "fontFamily": "Noto Sans CJK KR"
                    },
                    "data": [{"coord": [peak_x, peak_y]}] if peak_x is not None else []
                }
            }
        ]
    }

    figures.append({
        "name": clean_name(sheet_name),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
