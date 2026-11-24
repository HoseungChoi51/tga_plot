import json
import os
import re

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#5470C6", "#91CC75", "#EE6666"]


def clean_name(value):
    name = re.sub(r"[^\w가-힣-]+", "_", str(value).strip())
    return name.strip("_") or "plot"


def make_figure(sheet_name, frame, index):
    frame.columns = [str(column).strip() for column in frame.columns]

    temperature_col = next(
        (column for column in frame.columns if "temperature" in column.lower()),
        frame.columns[1],
    )
    weight_col = next(
        (column for column in frame.columns if "weight" in column.lower()),
        frame.columns[2],
    )
    x = pd.to_numeric(frame[temperature_col], errors="coerce")
    y = pd.to_numeric(frame[weight_col], errors="coerce")
    points = [
        [float(xv), float(yv)]
        for xv, yv in zip(x, y)
        if pd.notna(xv) and pd.notna(yv)
    ]

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 72, "right": 28, "top": 48, "bottom": 62},
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"fontSize": 15, "fontWeight": "normal"},
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "axisTick": {"inside": False, "length": 5},
            "axisLabel": {"fontSize": 9, "margin": 8},
            "nameTextStyle": {"fontSize": 11},
            "axisLine": {"lineStyle": {"color": "#444"}},
            "splitLine": {"show": False},
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisTick": {"inside": False, "length": 5},
            "axisLabel": {"fontSize": 9, "margin": 8},
            "nameTextStyle": {"fontSize": 11},
            "axisLine": {"lineStyle": {"color": "#444"}},
            "splitLine": {
                "show": True,
                "lineStyle": {"color": "#e6e6e6", "type": "solid"},
            },
        },
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "data": points,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.8, "color": COLORS[index % len(COLORS)]},
                "emphasis": {"disabled": True},
            }
        ],
    }

    return {
        "name": clean_name(sheet_name),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }


def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []
    for index, sheet_name in enumerate(workbook.sheet_names):
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        figures.append(make_figure(sheet_name, frame, index))
    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
