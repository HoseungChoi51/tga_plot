import json
import re
from pathlib import Path

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

TEXT_COLOR = "#808080"
FONT_SIZE = 13
PALETTE = ["#5470C6", "#91CC75", "#FAC858"]


def clean(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def make_option(sheet_name, frame, color):
    columns = {str(column).strip().lower(): column for column in frame.columns}
    temperature_col = next(
        (col for key, col in columns.items() if "temperature" in key or "temp" in key),
        frame.columns[1] if len(frame.columns) > 1 else frame.columns[0],
    )
    weight_col = next(
        (col for key, col in columns.items() if "weight" in key),
        frame.columns[2] if len(frame.columns) > 2 else frame.columns[-1],
    )
    derivative_col = next(
        (col for key, col in columns.items() if "d.w" in key or "derivative" in key or "dw" in key),
        frame.columns[3] if len(frame.columns) > 3 else None,
    )

    temperature = pd.to_numeric(frame[temperature_col], errors="coerce")
    weight = pd.to_numeric(frame[weight_col], errors="coerce")
    weight_data = [
        [clean(x), clean(y)]
        for x, y in zip(temperature, weight)
        if pd.notna(x) and pd.notna(y)
    ]

    series = [{
        "name": str(weight_col),
        "type": "line",
        "data": weight_data,
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": color},
        "itemStyle": {"color": color},
        "yAxisIndex": 0,
    }]

    y_axes = [{
        "type": "value",
        "name": str(weight_col),
        "nameTextStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
        "axisLabel": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
        "axisLine": {"lineStyle": {"color": TEXT_COLOR}},
        "splitLine": {"lineStyle": {"color": "#E6E6E6"}},
    }]
    legend_names = [str(weight_col)]

    if derivative_col is not None:
        derivative = pd.to_numeric(frame[derivative_col], errors="coerce")
        derivative_data = [
            [clean(x), clean(y)]
            for x, y in zip(temperature, derivative)
            if pd.notna(x) and pd.notna(y)
        ]
        series.append({
            "name": str(derivative_col),
            "type": "line",
            "data": derivative_data,
            "showSymbol": False,
            "lineStyle": {"width": 1.8, "color": "#EE6666"},
            "itemStyle": {"color": "#EE6666"},
            "yAxisIndex": 1,
        })
        y_axes.append({
            "type": "value",
            "name": str(derivative_col),
            "nameTextStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
            "axisLabel": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
            "axisLine": {"lineStyle": {"color": TEXT_COLOR}},
            "splitLine": {"show": False},
        })
        legend_names.append(str(derivative_col))

    return {
        "animation": False,
        "textStyle": {
            "color": TEXT_COLOR,
            "fontSize": FONT_SIZE,
            "fontFamily": "Noto Sans CJK KR, sans-serif",
        },
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
        },
        "tooltip": {
            "trigger": "axis",
            "textStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
        },
        "legend": {
            "data": legend_names,
            "top": 34,
            "textStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
        },
        "grid": {"left": 82, "right": 86, "top": 82, "bottom": 68},
        "xAxis": {
            "type": "value",
            "name": str(temperature_col),
            "nameLocation": "middle",
            "nameGap": 38,
            "nameTextStyle": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
            "axisLabel": {"color": TEXT_COLOR, "fontSize": FONT_SIZE},
            "axisLine": {"lineStyle": {"color": TEXT_COLOR}},
            "splitLine": {"lineStyle": {"color": "#E6E6E6"}},
        },
        "yAxis": y_axes,
        "series": series,
    }


path = Path(DATA_FILE)
workbook = pd.ExcelFile(path)
figures = []

for index, sheet_name in enumerate(workbook.sheet_names):
    frame = pd.read_excel(path, sheet_name=sheet_name)
    frame.columns = [str(column).strip() for column in frame.columns]
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", sheet_name).strip("_") or f"plot{index + 1}"

    figures.append({
        "name": safe_name,
        "option": make_option(sheet_name, frame, PALETTE[index % len(PALETTE)]),
        "width": 800,
        "height": 520,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
