import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
DPI = 300
WIDTH = 614
HEIGHT = 442


def clean_name(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def make_figure(sheet_name, frame):
    frame = frame.dropna(how="all").copy()
    frame.columns = [clean_name(c) for c in frame.columns]

    def find_column(patterns, fallback):
        for pattern in patterns:
            for col in frame.columns:
                if re.search(pattern, col, re.IGNORECASE):
                    return col
        return frame.columns[fallback] if len(frame.columns) > fallback else None

    x_col = find_column([r"temperature", r"temp", r"온도"], 1)
    y1_col = find_column([r"weight", r"wt", r"중량", r"무게"], 2)
    y2_col = find_column([r"\bd\.?\s*w\b", r"dtg", r"derivative", r"미분"], 3)

    if x_col is None or y1_col is None:
        raise ValueError(f"시트 '{sheet_name}'에서 온도/중량 열을 찾지 못했습니다.")

    x = pd.to_numeric(frame[x_col], errors="coerce").to_numpy(dtype=float)
    y1 = pd.to_numeric(frame[y1_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y1)
    x, y1 = x[valid], y1[valid]
    if not len(x):
        raise ValueError(f"시트 '{sheet_name}'에 유효한 데이터가 없습니다.")

    order = np.argsort(x)
    x, y1 = x[order], y1[order]
    y1_data = [[round(float(a), 6), round(float(b), 6)] for a, b in zip(x, y1)]

    series = [
        {
            "name": y1_col,
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "connectNulls": True,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": y1_data,
        }
    ]

    y2 = None
    if y2_col is not None:
        raw_x = pd.to_numeric(frame[x_col], errors="coerce").to_numpy(dtype=float)
        raw_y2 = pd.to_numeric(frame[y2_col], errors="coerce").to_numpy(dtype=float)
        valid2 = np.isfinite(raw_x) & np.isfinite(raw_y2)
        raw_x, raw_y2 = raw_x[valid2], raw_y2[valid2]
        order2 = np.argsort(raw_x)
        raw_x, raw_y2 = raw_x[order2], raw_y2[order2]
        y2 = -raw_y2
        series.append(
            {
                "name": y2_col,
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "connectNulls": True,
                "lineStyle": {"color": "green", "width": 2},
                "data": [
                    [round(float(a), 6), round(float(b), 6)]
                    for a, b in zip(raw_x, y2)
                ],
            }
        )

    residue_idx = int(np.argmin(np.abs(x - 800.0)))
    residue_x, residue = float(x[residue_idx]), float(y1[residue_idx])
    series[0]["markPoint"] = {
        "symbol": "circle",
        "symbolSize": 8,
        "itemStyle": {"color": "#1f4e9c"},
        "label": {
            "show": True,
            "formatter": f"Residue {residue:.1f}%",
            "position": "top",
            "color": "#333333",
            "fontFamily": "Noto Sans CJK KR",
        },
        "data": [{"coord": [residue_x, residue]}],
    }

    if y2 is not None and len(y2):
        peak_candidates = np.flatnonzero(raw_x > 150)
        if len(peak_candidates):
            peak_idx = int(peak_candidates[np.argmax(y2[peak_candidates])])
            peak_x, peak_y = float(raw_x[peak_idx]), float(y2[peak_idx])
            series[1]["markPoint"] = {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": "green"},
                "label": {
                    "show": True,
                    "formatter": f"{peak_x:.0f} °C",
                    "position": "top",
                    "color": "#333333",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [peak_x, peak_y]}],
            }

    option = {
        "animation": False,
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": [s["name"] for s in series],
            "left": "center",
            "top": "bottom",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        },
        "grid": {"left": 68, "right": 68, "top": 55, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": y1_col,
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
            },
            {
                "type": "value",
                "name": f"-{y2_col} (inverted)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "color": "green",
                },
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "color": "green",
                },
                "axisLine": {"show": True, "lineStyle": {"color": "green"}},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }
    return {
        "name": re.sub(r"[^A-Za-z0-9_-]+", "_", sheet_name).strip("_") or "plot",
        "option": option,
        "width": WIDTH,
        "height": HEIGHT,
        "dpi": DPI,
        "formats": ["png"],
    }


path = Path(DATA_FILE)
workbook = pd.ExcelFile(path)
figures = []
for sheet in workbook.sheet_names:
    data = pd.read_excel(path, sheet_name=sheet)
    figures.append(make_figure(sheet, data))

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
