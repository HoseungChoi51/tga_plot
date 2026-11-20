import json
import os
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_") or "plot"

def find_column(columns, pattern, fallback):
    for col in columns:
        if re.search(pattern, str(col), re.I):
            return col
    return columns[fallback] if len(columns) > fallback else None

def numeric(df, column):
    return pd.to_numeric(df[column], errors="coerce").to_numpy(dtype=float)

figures = []
workbook = pd.ExcelFile(DATA_FILE)

for sheet_name in workbook.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df = df.dropna(how="all")
    if df.empty:
        continue

    columns = list(df.columns)
    x_col = find_column(columns, r"temperature|temp|온도", 1)
    weight_col = find_column(columns, r"weight|mass|중량|무게", 2)
    dtg_col = find_column(columns, r"d\.?\s*w|dtg|derivative", 3)

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    x = numeric(df, x_col)
    weight = numeric(df, weight_col)
    dtg = numeric(df, dtg_col)
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if len(x) == 0:
        continue

    order = np.argsort(x, kind="stable")
    x, weight, dtg = x[order], weight[order], dtg[order]

    residue_idx = int(np.argmin(np.abs(x - 800.0)))
    residue_x, residue_y = float(x[residue_idx]), float(weight[residue_idx])

    peak_candidates = np.flatnonzero(x > 150.0)
    if len(peak_candidates):
        peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
    else:
        peak_idx = int(np.argmax(-dtg))
    peak_x = float(x[peak_idx])
    peak_y = float(-dtg[peak_idx])

    x_data = [float(v) for v in x]
    weight_data = [float(v) for v in weight]
    dtg_data = [float(-v) for v in dtg]

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "fontWeight": "normal"}
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Weight(%)", "-D.W(%/°C)"],
            "right": 18,
            "top": 42,
            "orient": "vertical",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 9}
        },
        "grid": {"left": 72, "right": 72, "top": 84, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 36,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
            },
            {
                "type": "value",
                "name": "-D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight(%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "data": [[xv, yv] for xv, yv in zip(x_data, weight_data)],
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_y:.1f}%",
                        "position": "right",
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 11
                    },
                    "data": [{"coord": [residue_x, residue_y]}]
                }
            },
            {
                "name": "-D.W(%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": [[xv, yv] for xv, yv in zip(x_data, dtg_data)],
                "lineStyle": {"color": "#c0392b", "width": 2},
                "itemStyle": {"color": "#c0392b"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": f"{peak_x:.0f} °C",
                        "position": "top",
                        "fontFamily": "Noto Sans CJK KR",
                        "fontSize": 11
                    },
                    "data": [{"coord": [peak_x, peak_y]}]
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
