import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_name(value):
    name = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", str(value).strip())
    return name.strip("_") or "plot"


def load_sheets(path):
    book = pd.ExcelFile(path)
    result = []
    for sheet_name in book.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet_name)
        frame = frame.dropna(how="all")
        if frame.empty:
            continue

        # TGA workbook columns: Time, Temperature, Weight(%), D.W(%/C)
        normalized = {str(c).strip().lower(): c for c in frame.columns}
        temp_col = next((normalized[k] for k in normalized if "temperature" in k), None)
        weight_col = next((normalized[k] for k in normalized if "weight" in k), None)
        derivative_col = next(
            (normalized[k] for k in normalized if "d.w" in k or "derivative" in k),
            None,
        )
        if temp_col is None or weight_col is None:
            numeric = frame.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric) < 2:
                continue
            temp_col, weight_col = numeric[1], numeric[2] if len(numeric) > 2 else numeric[1]

        x = pd.to_numeric(frame[temp_col], errors="coerce")
        weight = pd.to_numeric(frame[weight_col], errors="coerce")
        valid = x.notna() & weight.notna()

        data = {
            "x": x[valid].astype(float).tolist(),
            "weight": weight[valid].astype(float).tolist(),
        }
        if derivative_col is not None:
            derivative = pd.to_numeric(frame[derivative_col], errors="coerce")
            dvalid = x.notna() & derivative.notna()
            data["derivative"] = {
                "x": x[dvalid].astype(float).tolist(),
                "y": derivative[dvalid].astype(float).tolist(),
            }
        result.append((sheet_name, data))
    return result


def make_option(sheet_name, data):
    series = [
        {
            "name": "Weight(%)",
            "type": "line",
            "data": [[x, y] for x, y in zip(data["x"], data["weight"])],
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 0,
            "lineStyle": {"width": 2},
        }
    ]

    y_axes = [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"lineStyle": {"color": "#e5e7eb"}},
        }
    ]

    if "derivative" in data:
        derivative = data["derivative"]
        series.append(
            {
                "name": "D.W(%/C)",
                "type": "line",
                "data": [[x, y] for x, y in zip(derivative["x"], derivative["y"])],
                "showSymbol": False,
                "smooth": False,
                "yAxisIndex": 1,
                "lineStyle": {"width": 1.8},
            }
        )
        y_axes.append(
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "position": "right",
                "axisLabel": {"formatter": "{value}"},
                "splitLine": {"show": False},
            }
        )

    return {
        "backgroundColor": "#ffffff",
        "animation": False,
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
        "legend": {"top": 38, "data": [item["name"] for item in series]},
        "grid": {"left": 76, "right": 76 if len(y_axes) > 1 else 34, "top": 82, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": 900 if max(data["x"]) > 750 else 750,
            "axisLine": {"lineStyle": {"color": "#555"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#f0f0f0"}},
        },
        "yAxis": y_axes,
        "series": series,
    }


def main():
    path = Path(DATA_FILE)
    figures = []
    for index, (sheet_name, data) in enumerate(load_sheets(path), start=1):
        figures.append(
            {
                "name": f"{index}_{clean_name(sheet_name)}",
                "option": make_option(sheet_name, data),
                "width": 900,
                "height": 600,
                "dpi": 300,
                "formats": ["png"],
            }
        )
    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
