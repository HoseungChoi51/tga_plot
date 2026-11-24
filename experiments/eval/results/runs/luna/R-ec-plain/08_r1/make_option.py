import json
import re
from pathlib import Path

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#2563eb", "#dc2626", "#16a34a"]
WIDTH = 800
HEIGHT = 520


def clean_number(value):
    try:
        number = float(value)
        return number if pd.notna(number) else None
    except (TypeError, ValueError):
        return None


def safe_name(value):
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value)).strip("-")
    return name or "plot"


def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_index, sheet_name in enumerate(workbook.sheet_names):
        frame = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        frame.columns = [str(column).strip() for column in frame.columns]

        x_column = next(
            (column for column in frame.columns if "temperature" in column.lower()),
            frame.columns[1] if len(frame.columns) > 1 else frame.columns[0],
        )
        weight_column = next(
            (column for column in frame.columns if "weight" in column.lower() and "d.w" not in column.lower()),
            None,
        )
        derivative_column = next(
            (column for column in frame.columns if "d.w" in column.lower() or "derivative" in column.lower()),
            None,
        )

        if weight_column is None or derivative_column is None:
            numeric_columns = [
                column for column in frame.columns
                if pd.to_numeric(frame[column], errors="coerce").notna().any()
            ]
            candidates = [column for column in numeric_columns if column != x_column]
            if weight_column is None and candidates:
                weight_column = candidates[0]
            if derivative_column is None and len(candidates) > 1:
                derivative_column = candidates[1]

        if weight_column is None or derivative_column is None:
            continue

        data = []
        for _, row in frame.iterrows():
            x = clean_number(row.get(x_column))
            weight = clean_number(row.get(weight_column))
            derivative = clean_number(row.get(derivative_column))
            if x is not None and (weight is not None or derivative is not None):
                data.append((x, weight, derivative))

        if not data:
            continue

        color = COLORS[sheet_index % len(COLORS)]
        option = {
            "animation": False,
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "top": 12,
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
            },
            "legend": {
                "data": ["무게 (%)", "미분 무게 (%/°C)"],
                "top": 42,
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "grid": {"left": 76, "right": 78, "top": 88, "bottom": 66},
            "xAxis": {
                "type": "value",
                "name": "온도 (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "무게 (%)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "scale": True,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
                {
                    "type": "value",
                    "name": "미분 무게 (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 58,
                    "scale": True,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
            ],
            "series": [
                {
                    "name": "무게 (%)",
                    "type": "line",
                    "yAxisIndex": 0,
                    "showSymbol": False,
                    "lineStyle": {"width": 2, "color": color},
                    "data": [[x, weight] for x, weight, _ in data if weight is not None],
                },
                {
                    "name": "미분 무게 (%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "lineStyle": {"width": 2, "color": "#f59e0b"},
                    "data": [[x, derivative] for x, _, derivative in data if derivative is not None],
                },
            ],
        }

        figures.append(
            {
                "name": safe_name(sheet_name),
                "option": option,
                "width": WIDTH,
                "height": HEIGHT,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
