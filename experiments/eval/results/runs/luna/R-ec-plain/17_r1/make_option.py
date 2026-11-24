import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#2563eb", "#dc2626", "#16a34a"]
WIDTH = 768
HEIGHT = 480
DPI = 600


def clean_number(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_figure(sheet_name, frame, color):
    temperature = pd.to_numeric(frame["Temperature"], errors="coerce")
    weight = pd.to_numeric(frame["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(frame["D.W(%/C)"], errors="coerce")

    weight_data = [
        [clean_number(x), clean_number(y)]
        for x, y in zip(temperature, weight)
        if pd.notna(x) and pd.notna(y)
    ]
    derivative_data = [
        [clean_number(x), clean_number(y)]
        for x, y in zip(temperature, derivative)
        if pd.notna(x) and pd.notna(y)
    ]

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "title": {
            "text": f"TGA / DTG — {sheet_name}",
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "fontWeight": "normal"},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "top": 42,
            "data": ["Weight(%)", "D.W(%/C)"],
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        },
        "grid": {"left": 68, "right": 70, "top": 82, "bottom": 60},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 36,
            "min": 30,
            "max": None,
            "axisLine": {"lineStyle": {"color": "#555555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": color}},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": color},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#d97706"}},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#d97706"},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight(%)",
                "type": "line",
                "yAxisIndex": 0,
                "data": weight_data,
                "showSymbol": False,
                "lineStyle": {"width": 2, "color": color},
                "emphasis": {"focus": "series"},
            },
            {
                "name": "D.W(%/C)",
                "type": "line",
                "yAxisIndex": 1,
                "data": derivative_data,
                "showSymbol": False,
                "lineStyle": {"width": 1.6, "color": "#d97706"},
                "emphasis": {"focus": "series"},
            },
        ],
    }

    return {
        "name": f"tga_{sheet_name.replace(' ', '_').replace('/', '-')}",
        "option": option,
        "width": WIDTH,
        "height": HEIGHT,
        "dpi": DPI,
        "formats": ["png"],
    }


workbook = pd.ExcelFile(DATA_FILE)
figures = []

for index, sheet_name in enumerate(workbook.sheet_names):
    frame = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    required = {"Temperature", "Weight(%)", "D.W(%/C)"}
    if required.issubset(frame.columns):
        figures.append(make_figure(sheet_name, frame, COLORS[index % len(COLORS)]))

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
