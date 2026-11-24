import json
import os
import re
import sys

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE"]
FIGURES = []


def clean_name(value):
    name = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", str(value)).strip("_")
    return name or "plot"


def make_figure(sheet_name, frame, color):
    columns = {str(c).strip().lower(): c for c in frame.columns}
    x_col = next((columns[k] for k in columns if "temperature" in k), frame.columns[1])
    weight_col = next((columns[k] for k in columns if "weight" in k), frame.columns[2])
    derivative_col = next(
        (columns[k] for k in columns if "d.w" in k or "derivative" in k or "dtg" in k),
        frame.columns[3] if len(frame.columns) > 3 else None,
    )

    data = []
    for _, row in frame.iterrows():
        try:
            x = float(row[x_col])
            weight = float(row[weight_col])
            if not (pd.notna(x) and pd.notna(weight)):
                continue
            point = [x, weight]
            if derivative_col is not None:
                value = pd.to_numeric(row[derivative_col], errors="coerce")
                point.append(float(value) if pd.notna(value) else None)
            data.append(point)
        except (TypeError, ValueError):
            continue

    if not data:
        return

    series = [
        {
            "name": str(weight_col),
            "type": "line",
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": color},
            "data": [[p[0], p[1]] for p in data],
            "markLine": {
                "symbol": ["none", "none"],
                "silent": True,
                "lineStyle": {"color": "#D62728", "width": 2, "type": "dashed"},
                "label": {
                    "show": True,
                    "formatter": "산화 시작",
                    "position": "insideEndTop",
                    "color": "#D62728",
                    "fontSize": 13,
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"xAxis": 450}],
            },
        }
    ]

    if len(data[0]) > 2 and any(p[2] is not None for p in data):
        series.append(
            {
                "name": str(derivative_col),
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "lineStyle": {"width": 1.6, "color": "#333333"},
                "data": [[p[0], p[2]] for p in data],
            }
        )

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontSize": 16, "fontWeight": "normal"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 30, "data": [s["name"] for s in series]},
        "grid": {"left": 72, "right": 72 if len(series) > 1 else 30, "top": 76, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": str(x_col) + " (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": max(900, max(p[0] for p in data)),
            "axisLine": {"lineStyle": {"color": "#666666"}},
            "splitLine": {"lineStyle": {"color": "#E8E8E8"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": str(weight_col),
                "nameLocation": "middle",
                "nameGap": 48,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": "#666666"}},
                "splitLine": {"lineStyle": {"color": "#E8E8E8"}},
            }
        ],
        "series": series,
    }

    if len(series) > 1:
        option["yAxis"].append(
            {
                "type": "value",
                "name": str(derivative_col),
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#666666"}},
                "splitLine": {"show": False},
            }
        )

    FIGURES.append(
        {
            "name": clean_name(sheet_name),
            "option": option,
            "width": 900,
            "height": 560,
            "dpi": 300,
            "formats": ["png"],
        }
    )


def main():
    path = os.environ.get("DATA_FILE", DATA_FILE)
    if not os.path.isfile(path):
        paths = os.environ.get("DATA_FILES", "")
        path = paths.split(os.pathsep)[0] if paths else path

    if path.lower().endswith((".xlsx", ".xls")):
        sheets = pd.read_excel(path, sheet_name=None)
    elif path.lower().endswith(".csv"):
        sheets = {os.path.splitext(os.path.basename(path))[0]: pd.read_csv(path)}
    else:
        sheets = {os.path.splitext(os.path.basename(path))[0]: pd.read_csv(path, sep=None, engine="python")}

    for index, (sheet_name, frame) in enumerate(sheets.items()):
        make_figure(sheet_name, frame, COLORS[index % len(COLORS)])

    print(json.dumps({"figures": FIGURES}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
