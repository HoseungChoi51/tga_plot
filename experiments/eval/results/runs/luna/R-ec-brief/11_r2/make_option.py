import json
import os
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

BLUE = "#1f4e9c"
RED = "#c0392b"
TEXT = "#333333"
GRID = "#d9d9d9"


def clean_name(value):
    return str(value).strip() if value is not None else ""


def make_figure(sheet_name, frame):
    frame = frame.dropna(how="all").copy()
    frame.columns = [clean_name(c) for c in frame.columns]

    def find_column(names, fallback):
        for col in frame.columns:
            normalized = col.lower().replace(" ", "")
            if any(name in normalized for name in names):
                return col
        return frame.columns[fallback] if len(frame.columns) > fallback else None

    x_col = find_column(["temperature", "temp"], 1)
    weight_col = find_column(["weight", "mass"], 2)
    dtg_col = find_column(["d.w", "dtg", "derivative"], 3)

    if x_col is None or weight_col is None:
        return None

    x = pd.to_numeric(frame[x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(frame[weight_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(weight)
    x, weight = x[valid], weight[valid]

    if not len(x):
        return None

    order = np.argsort(x)
    x, weight = x[order], weight[order]

    weight_data = [[float(a), float(b)] for a, b in zip(x, weight)]

    series = [
        {
            "name": clean_name(weight_col),
            "type": "line",
            "data": weight_data,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": BLUE},
            "yAxisIndex": 0,
            "connectNulls": True,
        }
    ]

    if dtg_col is not None:
        dtg = pd.to_numeric(frame[dtg_col], errors="coerce").to_numpy(dtype=float)
        dtg = dtg[valid][order]
        dtg_valid = np.isfinite(dtg)
        dtg_data = [
            [float(a), float(-b)]
            for a, b, ok in zip(x, dtg, dtg_valid)
            if ok
        ]
        series.append(
            {
                "name": clean_name(dtg_col),
                "type": "line",
                "data": dtg_data,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.8, "color": RED},
                "yAxisIndex": 1,
                "connectNulls": True,
            }
        )

    residue_idx = int(np.argmin(np.abs(x - 800)))
    residue = float(weight[residue_idx])

    series.append(
        {
            "name": "Residue",
            "type": "scatter",
            "data": [[float(x[residue_idx]), residue]],
            "symbolSize": 8,
            "itemStyle": {"color": BLUE},
            "yAxisIndex": 0,
            "label": {
                "show": True,
                "formatter": f"Residue {residue:.1f}%",
                "position": "right",
                "color": BLUE,
                "fontSize": 12,
            },
        }
    )

    option = {
        "animation": False,
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "color": TEXT},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": [clean_name(weight_col)] + ([clean_name(dtg_col)] if dtg_col else []),
            "left": "center",
            "bottom": 4,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "color": TEXT},
        },
        "grid": {"left": 72, "right": 72, "top": 60, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": clean_name(x_col),
            "nameLocation": "middle",
            "nameGap": 32,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "splitLine": {"show": False},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": TEXT},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": TEXT},
        },
        "yAxis": [
            {
                "type": "value",
                "name": clean_name(weight_col),
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": BLUE}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": BLUE},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": BLUE},
                "splitLine": {"show": True, "lineStyle": {"color": GRID}},
            },
            {
                "type": "value",
                "name": clean_name(dtg_col) if dtg_col else "DTG",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": RED}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR", "color": RED},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": RED},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    return {
        "name": f"tga_{len(sheet_name)}_{sheet_name}".replace("/", "_").replace("\\", "_"),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }


figures = []
excel = pd.ExcelFile(DATA_FILE)
for sheet in excel.sheet_names:
    data = pd.read_excel(DATA_FILE, sheet_name=sheet)
    figure = make_figure(sheet, data)
    if figure:
        figures.append(figure)

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
