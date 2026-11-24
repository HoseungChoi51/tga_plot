import json
import os
import re

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    name = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", str(value).strip())
    return name.strip("_") or "plot"

def find_column(columns, patterns, fallback=None):
    for pattern in patterns:
        for col in columns:
            if re.search(pattern, str(col), re.I):
                return col
    return fallback

def finite_pairs(x, y):
    pairs = []
    for xv, yv in zip(x, y):
        try:
            xv, yv = float(xv), float(yv)
        except (TypeError, ValueError):
            continue
        if np.isfinite(xv) and np.isfinite(yv):
            pairs.append([xv, yv])
    return pairs

figures = []
sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    if df.empty:
        continue

    x_col = find_column(df.columns, [r"temperature", r"temp", r"온도"], df.columns[1] if len(df.columns) > 1 else df.columns[0])
    weight_col = find_column(df.columns, [r"weight", r"mass", r"중량", r"무게"], df.columns[2] if len(df.columns) > 2 else None)
    dtg_col = find_column(df.columns, [r"dtg", r"d\.?\s*w", r"derivative"], df.columns[3] if len(df.columns) > 3 else None)
    if weight_col is None:
        continue

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
    weight_data = finite_pairs(x, weight)

    series = [{
        "name": str(weight_col),
        "type": "line",
        "yAxisIndex": 0,
        "data": weight_data,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"color": "#1f4e9c", "width": 2},
        "emphasis": {"focus": "series"},
        "markArea": {
            "silent": True,
            "itemStyle": {"color": "rgba(190, 190, 190, 0.28)"},
            "data": [[{"xAxis": 300}, {"xAxis": 450}]]
        }
    }]

    if dtg_col is not None:
        dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()
        # TGA derivative is negative during mass loss; invert it so peaks point upward.
        dtg_data = finite_pairs(x, -dtg)
        series.append({
            "name": str(dtg_col) + " (−)",
            "type": "line",
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": "#c0392b", "width": 1.8},
            "emphasis": {"focus": "series"}
        })

    valid = np.isfinite(x) & np.isfinite(weight)
    residue_text = None
    residue_point = None
    if valid.any():
        inds = np.flatnonzero(valid)
        idx = inds[np.argmin(np.abs(x[inds] - 800))]
        residue_point = [float(x[idx]), float(weight[idx])]
        residue_text = f"Residue {weight[idx]:.1f}%"

    peak_text = None
    peak_point = None
    if dtg_col is not None:
        dvalid = np.isfinite(x) & np.isfinite(dtg) & (x > 150)
        if dvalid.any():
            inds = np.flatnonzero(dvalid)
            idx = inds[np.argmax(-dtg[inds])]
            peak_point = [float(x[idx]), float(-dtg[idx])]
            peak_text = f"{x[idx]:.0f} °C"

    if residue_point:
        series[0]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#1f4e9c", "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": residue_text,
                "position": "right",
                "color": "#1f4e9c",
                "fontFamily": "Noto Sans CJK KR"
            },
            "data": [{"coord": residue_point}]
        }
    if peak_point and len(series) > 1:
        series[1]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 8,
            "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": peak_text,
                "position": "top",
                "color": "#c0392b",
                "fontFamily": "Noto Sans CJK KR"
            },
            "data": [{"coord": peak_point}]
        }

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"left": "center", "bottom": 8, "textStyle": {"fontFamily": "Noto Sans CJK KR"}},
        "grid": {"left": 72, "right": 72, "top": 60, "bottom": 72},
        "xAxis": {
            "type": "value",
            "name": str(x_col) + " (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "splitLine": {"show": False}
        },
        "yAxis": [
            {
                "type": "value",
                "name": str(weight_col) + " (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisLabel": {"color": "#1f4e9c"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
            },
            {
                "type": "value",
                "name": "−" + str(dtg_col) if dtg_col is not None else "DTG",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisLabel": {"color": "#c0392b"},
                "splitLine": {"show": False}
            }
        ],
        "series": series
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
