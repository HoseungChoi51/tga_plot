import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
WIDTH = 614
HEIGHT = 442
DPI = 300


def clean(value):
    if pd.isna(value):
        return None
    try:
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def find_column(columns, pattern, fallback):
    for column in columns:
        if re.search(pattern, str(column), re.IGNORECASE):
            return column
    return columns[fallback] if len(columns) > fallback else None


def make_figure(sheet_name, frame):
    columns = list(frame.columns)
    x_col = find_column(columns, r"temperature|temp|온도", 1)
    weight_col = find_column(columns, r"weight|mass|중량|무게", 2)
    dtg_col = find_column(columns, r"d\.?\s*w|dtg|derivative|미분", 3)

    x = pd.to_numeric(frame[x_col], errors="coerce")
    weight = pd.to_numeric(frame[weight_col], errors="coerce")
    dtg = pd.to_numeric(frame[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna()
    x_values = x[valid].to_numpy(dtype=float)
    weight_values = weight[valid].to_numpy(dtype=float)

    dtg_valid = x.notna() & dtg.notna()
    dtg_x = x[dtg_valid].to_numpy(dtype=float)
    dtg_values = dtg[dtg_valid].to_numpy(dtype=float)

    residue_x = None
    residue = None
    if len(x_values):
        idx = int(np.argmin(np.abs(x_values - 800.0)))
        residue_x = float(x_values[idx])
        residue = float(weight_values[idx])

    peak_x = None
    peak_y = None
    peak_candidates = np.flatnonzero(dtg_x > 150) if len(dtg_x) else []
    if len(peak_candidates):
        candidate_idx = peak_candidates[int(np.argmax(-dtg_values[peak_candidates]))]
        peak_x = float(dtg_x[candidate_idx])
        peak_y = float(-dtg_values[candidate_idx])

    weight_data = [[float(a), float(b)] for a, b in zip(x_values, weight_values)]
    dtg_data = [[float(a), float(-b)] for a, b in zip(dtg_x, dtg_values)]

    series = [
        {
            "name": str(weight_col),
            "type": "line",
            "data": weight_data,
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 0,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "itemStyle": {"color": "#1f4e9c"},
        },
        {
            "name": str(dtg_col) + " (-DTG)",
            "type": "line",
            "data": dtg_data,
            "showSymbol": False,
            "smooth": False,
            "yAxisIndex": 1,
            "lineStyle": {"width": 2, "color": "#c0392b"},
            "itemStyle": {"color": "#c0392b"},
        },
    ]

    annotations = []
    if residue is not None:
        annotations.append(
            {
                "name": "Residue",
                "type": "scatter",
                "yAxisIndex": 0,
                "data": [[residue_x, residue]],
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c", "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue:.1f}%",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontSize": 11,
                },
                "tooltip": {"show": False},
                "z": 5,
            }
        )
    if peak_x is not None:
        annotations.append(
            {
                "name": "DTG peak",
                "type": "scatter",
                "yAxisIndex": 1,
                "data": [[peak_x, peak_y]],
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"{peak_x:.0f} °C",
                    "position": "top",
                    "color": "#c0392b",
                    "fontSize": 11,
                },
                "tooltip": {"show": False},
                "z": 5,
            }
        )
    series.extend(annotations)

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 8,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "fontWeight": "normal"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [str(weight_col), str(dtg_col) + " (-DTG)"], "left": 75, "top": "middle"},
        "grid": {"left": 75, "right": 75, "top": 55, "bottom": 55},
        "xAxis": {
            "type": "value",
            "name": str(x_col),
            "nameLocation": "middle",
            "nameGap": 32,
            "axisTick": {"inside": False},
            "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": str(weight_col),
                "position": "left",
                "axisTick": {"inside": False},
                "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
            },
            {
                "type": "value",
                "name": "- " + str(dtg_col),
                "position": "right",
                "axisTick": {"inside": False},
                "axisLabel": {"fontSize": 9, "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }
    return {
        "name": re.sub(r"[^A-Za-z0-9_-]+", "_", str(sheet_name)).strip("_") or "plot",
        "option": option,
        "width": WIDTH,
        "height": HEIGHT,
        "dpi": DPI,
        "formats": ["png"],
    }


def main():
    path = Path(DATA_FILE)
    figures = []
    if path.suffix.lower() in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None)
        for name, frame in sheets.items():
            figures.append(make_figure(name, frame))
    elif path.suffix.lower() == ".csv":
        figures.append(make_figure(path.stem, pd.read_csv(path)))
    else:
        figures.append(make_figure(path.stem, pd.read_csv(path, sep=None, engine="python")))

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
