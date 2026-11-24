import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
WIDTH = 900
HEIGHT = 560
DPI = 300


def clean_number(value):
    try:
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def load_sheets(path):
    workbook = pd.ExcelFile(path)
    sheets = []
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet_name)
        frame.columns = [str(column).strip() for column in frame.columns]
        sheets.append((sheet_name, frame))
    return sheets


figures = []
for index, (sheet_name, frame) in enumerate(load_sheets(DATA_FILE), start=1):
    columns = {str(column).strip().lower(): column for column in frame.columns}

    x_column = next((columns[key] for key in columns if "temperature" in key), None)
    weight_column = next(
        (columns[key] for key in columns if "weight" in key), None
    )
    derivative_column = next(
        (columns[key] for key in columns if "d.w" in key or "derivative" in key),
        None,
    )

    if x_column is None:
        x_column = frame.columns[1] if len(frame.columns) > 1 else frame.columns[0]
    if weight_column is None:
        weight_column = frame.columns[2] if len(frame.columns) > 2 else None
    if derivative_column is None:
        derivative_column = frame.columns[3] if len(frame.columns) > 3 else None

    series = []
    legend = []
    y_axes = [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
        }
    ]

    if weight_column is not None:
        data = []
        for x, y in zip(frame[x_column], frame[weight_column]):
            xn, yn = clean_number(x), clean_number(y)
            if xn is not None and yn is not None:
                data.append([xn, yn])
        series.append(
            {
                "name": "Weight (%)",
                "type": "line",
                "data": data,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 2, "color": "#2563eb"},
                "yAxisIndex": 0,
                "sampling": "lttb",
            }
        )
        legend.append("Weight (%)")

    if derivative_column is not None:
        data = []
        for x, y in zip(frame[x_column], frame[derivative_column]):
            xn, yn = clean_number(x), clean_number(y)
            if xn is not None and yn is not None:
                data.append([xn, yn])
        y_axes.append(
            {
                "type": "value",
                "name": "D.W. (%/°C)",
                "nameLocation": "middle",
                "nameGap": 55,
                "position": "right",
                "axisLine": {"show": True},
                "splitLine": {"show": False},
            }
        )
        series.append(
            {
                "name": "D.W. (%/°C)",
                "type": "line",
                "data": data,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.7, "color": "#dc2626"},
                "yAxisIndex": 1,
                "sampling": "lttb",
            }
        )
        legend.append("D.W. (%/°C)")

    option = {
        "backgroundColor": "#ffffff",
        "title": {
            "text": sheet_name,
            "left": "center",
            "top": 10,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "data": legend,
            "top": 10,
            "right": 16,
            "orient": "horizontal",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 9},
        },
        "grid": {"left": 76, "right": 78, "top": 58, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": 900 if "750c" not in sheet_name.lower() else 750,
            "axisLine": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#f0f0f0"}},
        },
        "yAxis": y_axes,
        "series": series,
    }

    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", sheet_name).strip("_").lower()
    figures.append(
        {
            "name": safe_name or f"plot{index}",
            "option": option,
            "width": WIDTH,
            "height": HEIGHT,
            "dpi": DPI,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
