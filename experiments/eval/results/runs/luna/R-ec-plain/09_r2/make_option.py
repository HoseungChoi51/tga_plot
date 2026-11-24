import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_number(value):
    if pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def safe_name(name):
    text = re.sub(r"[^\w가-힣.-]+", "_", str(name).strip())
    return text.strip("_") or "plot"


def load_sheets(path):
    suffix = Path(path).suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=None)
    if suffix == ".csv":
        return {Path(path).stem: pd.read_csv(path)}
    return {Path(path).stem: pd.read_csv(path, sep=None, engine="python", comment="#")}


def make_option(sheet_name, df):
    columns = {str(col).strip().lower(): col for col in df.columns}
    x_col = next((columns[k] for k in columns if "temperature" in k or k in ("temp", "온도")), None)
    weight_col = next((columns[k] for k in columns if "weight" in k or "무게" in k), None)
    derivative_col = next((columns[k] for k in columns if "d.w" in k or "derivative" in k or "dw" == k), None)

    if x_col is None and len(df.columns) > 1:
        x_col = df.columns[1]
    if weight_col is None and len(df.columns) > 2:
        weight_col = df.columns[2]
    if derivative_col is None and len(df.columns) > 3:
        derivative_col = df.columns[3]

    x = pd.to_numeric(df[x_col], errors="coerce") if x_col is not None else pd.Series(dtype=float)
    weight = pd.to_numeric(df[weight_col], errors="coerce") if weight_col is not None else pd.Series(dtype=float)
    derivative = pd.to_numeric(df[derivative_col], errors="coerce") if derivative_col is not None else pd.Series(dtype=float)

    weight_data = []
    derivative_data = []
    for xv, yv in zip(x, weight):
        if pd.notna(xv) and pd.notna(yv):
            weight_data.append([clean_number(xv), clean_number(yv)])
    for xv, yv in zip(x, derivative):
        if pd.notna(xv) and pd.notna(yv):
            derivative_data.append([clean_number(xv), clean_number(yv)])

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 15, "fontWeight": "normal"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 40, "data": ["Weight(%)", "D.W(%/C)"]},
        "grid": {"left": 72, "right": 76, "top": 82, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "axisTick": {"inside": False, "length": 5},
            "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
            "axisLine": {"lineStyle": {"color": "#555555"}},
            "splitLine": {"show": False},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisTick": {"inside": False, "length": 5},
                "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
                "axisLine": {"show": True, "lineStyle": {"color": "#2878b5"}},
                "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisTick": {"inside": False, "length": 5},
                "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
                "axisLine": {"show": True, "lineStyle": {"color": "#d9534f"}},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight(%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "data": weight_data,
                "lineStyle": {"width": 1.5, "color": "#2878b5"},
            },
            {
                "name": "D.W(%/C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": derivative_data,
                "lineStyle": {"width": 1.3, "color": "#d9534f"},
            },
        ],
    }
    return option


sheets = load_sheets(DATA_FILE)
figures = []
used_names = set()

for sheet_name, frame in sheets.items():
    name = safe_name(sheet_name)
    base = name
    index = 2
    while name in used_names:
        name = f"{base}_{index}"
        index += 1
    used_names.add(name)
    figures.append(
        {
            "name": name,
            "option": make_option(sheet_name, frame),
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
