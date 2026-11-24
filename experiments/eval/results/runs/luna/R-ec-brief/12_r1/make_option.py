import json
import os
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    name = re.sub(r"[^\w\-]+", "_", str(value).strip(), flags=re.UNICODE).strip("_")
    return name or "plot"

def series_data(x, y):
    pairs = []
    for xv, yv in zip(x, y):
        if pd.notna(xv) and pd.notna(yv):
            pairs.append([float(xv), float(yv)])
    return pairs

def build_option(sheet_name, frame):
    cols = list(frame.columns)

    def find_col(pattern, fallback):
        for col in cols:
            if re.search(pattern, str(col), re.I):
                return col
        return cols[fallback] if len(cols) > fallback else None

    xcol = find_col(r"temperature|temp|온도", 1)
    wcol = find_col(r"weight|mass|무게|중량", 2)
    dcol = find_col(r"d\.?\s*w|dtg|derivative|미분", 3)

    x = pd.to_numeric(frame[xcol], errors="coerce")
    weight = pd.to_numeric(frame[wcol], errors="coerce")
    dtg = pd.to_numeric(frame[dcol], errors="coerce")

    weight_data = series_data(x, weight)
    dtg_data = series_data(x, -dtg)

    residue = None
    valid_w = pd.DataFrame({"x": x, "y": weight}).dropna()
    if not valid_w.empty:
        near = valid_w.loc[(valid_w["x"] - 800).abs().idxmin()]
        residue = [float(near["x"]), float(near["y"])]

    peak = None
    valid_d = pd.DataFrame({"x": x, "y": dtg}).dropna()
    valid_d = valid_d[valid_d["x"] > 150]
    if not valid_d.empty:
        row = valid_d.loc[valid_d["y"].idxmin()]
        peak = [float(row["x"]), float(-row["y"])]

    all_w = [p[1] for p in weight_data]
    all_d = [p[1] for p in dtg_data]
    y1_min = min(0.0, min(all_w)) if all_w else 0
    y1_max = max(105.0, max(all_w) * 1.05) if all_w else 105
    y2_max = max(all_d) * 1.15 if all_d else 1
    if y2_max <= 0:
        y2_max = 1

    series = [
        {
            "name": str(wcol),
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "data": weight_data,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "data": [
                    {
                        "coord": residue,
                        "name": f"Residue {residue[1]:.1f}%",
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue[1]:.1f}%",
                            "position": "right",
                        },
                    }
                ],
            } if residue else {},
        },
        {
            "name": str(dcol),
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": dtg_data,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "data": [
                    {
                        "coord": peak,
                        "name": f"{peak[0]:.0f} °C",
                        "label": {
                            "show": True,
                            "formatter": f"{peak[0]:.0f} °C",
                            "position": "top",
                        },
                    }
                ],
            } if peak else {},
        },
        {
            "name": "산화 시작",
            "type": "line",
            "yAxisIndex": 0,
            "data": [],
            "showSymbol": False,
            "silent": True,
            "markLine": {
                "symbol": ["none", "none"],
                "lineStyle": {"color": "#555555", "type": "dashed", "width": 1.5},
                "label": {
                    "show": True,
                    "formatter": "산화 시작",
                    "position": "insideEndTop",
                    "color": "#333333",
                },
                "data": [{"xAxis": 450}],
            },
        },
    ]

    return {
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [str(wcol), str(dcol)], "left": "center", "top": 32},
        "grid": {"left": 68, "right": 68, "top": 78, "bottom": 58},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": 30,
            "max": 900,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "min": y1_min,
                "max": y1_max,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "min": 0,
                "max": y2_max,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
        ],
        "series": series,
    }

book = pd.ExcelFile(DATA_FILE)
figures = []
for sheet in book.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df = df.dropna(how="all")
    if df.empty or len(df.columns) < 4:
        continue
    figures.append({
        "name": clean_name(sheet),
        "option": build_option(sheet, df),
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
