import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    return re.sub(r"[\x00-\x1f\\/:*?\"<>|]+", "_", str(value)).strip(" ._") or "plot"

def find_column(columns, terms):
    lowered = [str(c).strip().lower() for c in columns]
    for term in terms:
        for idx, name in enumerate(lowered):
            if term in name:
                return columns[idx]
    return None

def finite_xy(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]

figures = []
path = Path(DATA_FILE)

book = pd.ExcelFile(path)
for sheet_name in book.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet_name)
    if df.empty:
        continue

    xcol = find_column(df.columns, ["temperature", "temp", "°c", "°"])
    y1col = find_column(df.columns, ["weight", "mass"])
    y2col = find_column(df.columns, ["d.w", "dtg", "derivative", "dw"])

    numeric = df.apply(pd.to_numeric, errors="coerce")
    if xcol is None or y1col is None:
        cols = [c for c in numeric.columns if numeric[c].notna().sum() > 0]
        if len(cols) < 2:
            continue
        xcol = xcol or cols[0]
        y1col = y1col or cols[1]
    if y2col is None:
        candidates = [c for c in numeric.columns if c not in (xcol, y1col) and numeric[c].notna().sum() > 0]
        y2col = candidates[0] if candidates else None

    x = numeric[xcol].to_numpy(dtype=float)
    y1 = numeric[y1col].to_numpy(dtype=float)
    x1, y1 = finite_xy(x, y1)
    if len(x1) == 0:
        continue

    data1 = [[float(a), float(b)] for a, b in zip(x1, y1)]
    series = [{
        "name": str(y1col),
        "type": "line",
        "yAxisIndex": 0,
        "data": data1,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"color": "#000000", "width": 2.5},
        "itemStyle": {"color": "#000000"},
        "connectNulls": True
    }]

    y2_values = None
    if y2col is not None:
        raw_y2 = numeric[y2col].to_numpy(dtype=float)
        x2, raw_y2 = finite_xy(x, raw_y2)
        y2_values = -raw_y2
        series.append({
            "name": str(y2col),
            "type": "line",
            "yAxisIndex": 1,
            "data": [[float(a), float(b)] for a, b in zip(x2, y2_values)],
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": "#c0392b", "width": 1.5, "type": "dashed"},
            "itemStyle": {"color": "#c0392b"},
            "connectNulls": True
        })

    annotations = []
    near800 = int(np.argmin(np.abs(x1 - 800.0)))
    residue_x, residue_y = float(x1[near800]), float(y1[near800])
    annotations.append({
        "name": "Residue",
        "coord": [residue_x, residue_y],
        "value": f"Residue {residue_y:.1f}%",
        "itemStyle": {"color": "#000000"},
        "label": {"show": True, "formatter": f"Residue {residue_y:.1f}%", "position": "top"}
    })

    peak_x = None
    if y2_values is not None and len(y2_values):
        # Peak at the highest positive DTG value above 150 °C.
        x2 = x[np.isfinite(x) & np.isfinite(numeric[y2col].to_numpy(dtype=float))]
        eligible = np.where(x2 > 150.0)[0]
        if len(eligible):
            peak_idx = eligible[np.argmax(y2_values[eligible])]
            peak_x = float(x2[peak_idx])
            peak_y = float(y1[np.argmin(np.abs(x1 - peak_x))])
            annotations.append({
                "name": "DTG peak",
                "coord": [peak_x, peak_y],
                "value": f"{peak_x:.0f} °C",
                "itemStyle": {"color": "#c0392b"},
                "label": {"show": True, "formatter": f"{peak_x:.0f} °C", "position": "top"}
            })

    option = {
        "animation": False,
        "title": {"text": str(sheet_name), "left": "center"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [str(y1col)] + ([str(y2col)] if y2col is not None else []), "left": "center"},
        "grid": {"left": 75, "right": 75, "top": 75, "bottom": 60},
        "xAxis": {
            "type": "value",
            "name": str(xcol),
            "nameLocation": "middle",
            "nameGap": 34,
            "scale": True
        },
        "yAxis": [
            {
                "type": "value",
                "name": str(y1col),
                "nameLocation": "middle",
                "nameGap": 52,
                "scale": True
            },
            {
                "type": "value",
                "name": str(y2col) if y2col is not None else "DTG (-)",
                "nameLocation": "middle",
                "nameGap": 52,
                "scale": True
            }
        ],
        "series": series
    }

    # Plot standard residue and peak markers in their respective coordinate systems.
    series[0]["markPoint"] = {
        "symbol": "circle",
        "symbolSize": 8,
        "data": [{
            "coord": [residue_x, residue_y],
            "name": "Residue",
            "value": f"Residue {residue_y:.1f}%",
            "itemStyle": {"color": "#000000"},
            "label": {"show": True, "formatter": f"Residue {residue_y:.1f}%", "position": "top"}
        }]
    }
    if peak_x is not None:
        peak_i = int(np.argmin(np.abs(x1 - peak_x)))
        peak_y = float(y1[peak_i])
        series[0]["markPoint"]["data"].append({
            "coord": [peak_x, peak_y],
            "name": "DTG peak",
            "value": f"{peak_x:.0f} °C",
            "itemStyle": {"color": "#c0392b"},
            "label": {"show": True, "formatter": f"{peak_x:.0f} °C", "position": "bottom"}
        })

    figures.append({
        "name": clean_name(sheet_name),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
