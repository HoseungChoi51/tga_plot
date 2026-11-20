import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = {"weight": "#000000", "dtg": "#c0392b"}
WIDTH = 2.5


def clean_name(value):
    return re.sub(r"[\x00-\x1f]", "", str(value)).strip()


def find_column(columns, patterns, fallback):
    for pattern in patterns:
        for i, name in enumerate(columns):
            if re.search(pattern, str(name), re.I):
                return i
    return fallback


def option_for_sheet(sheet_name, frame):
    frame = frame.dropna(how="all").copy()
    if frame.empty or frame.shape[1] < 3:
        return None

    columns = list(frame.columns)
    x_idx = find_column(columns, [r"temperature", r"temp", r"온도"], 1)
    weight_idx = find_column(columns, [r"weight", r"mass", r"중량", r"무게"], 2)
    dtg_idx = find_column(columns, [r"\bd\.?\s*w\b", r"dtg", r"derivative", r"미분"], 3)

    if x_idx >= len(columns) or weight_idx >= len(columns):
        return None
    if dtg_idx >= len(columns):
        dtg_idx = None

    x = pd.to_numeric(frame.iloc[:, x_idx], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(frame.iloc[:, weight_idx], errors="coerce").to_numpy(dtype=float)

    if dtg_idx is not None:
        dtg = pd.to_numeric(frame.iloc[:, dtg_idx], errors="coerce").to_numpy(dtype=float)
    else:
        dtg = np.full(len(x), np.nan)

    valid_xw = np.isfinite(x) & np.isfinite(weight)
    x, weight, dtg = x[valid_xw], weight[valid_xw], dtg[valid_xw]
    if not len(x):
        return None

    order = np.argsort(x, kind="stable")
    x, weight, dtg = x[order], weight[order], dtg[order]

    weight_data = [[round(float(a), 6), round(float(b), 6)] for a, b in zip(x, weight)]
    dtg_valid = np.isfinite(dtg)
    dtg_data = [[round(float(a), 6), round(float(-b), 6)] for a, b in zip(x[dtg_valid], dtg[dtg_valid])]

    residue_idx = int(np.argmin(np.abs(x - 800.0)))
    residue_x, residue_y = float(x[residue_idx]), float(weight[residue_idx])

    peak_candidates = np.flatnonzero((x > 150.0) & np.isfinite(dtg))
    if len(peak_candidates):
        peak_idx = int(peak_candidates[np.argmin(dtg[peak_candidates])])
        peak_x, peak_y = float(x[peak_idx]), float(-dtg[peak_idx])
        peak_label = f"{peak_x:.0f} °C"
    else:
        peak_x = peak_y = None
        peak_label = ""

    series = [
        {
            "name": str(columns[weight_idx]),
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"color": COLORS["weight"], "width": WIDTH},
            "itemStyle": {"color": COLORS["weight"]},
            "data": weight_data,
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": COLORS["weight"]},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_y:.1f}%",
                    "position": "top",
                    "color": "#333333",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [residue_x, residue_y]}],
            },
        }
    ]

    if dtg_idx is not None and dtg_data:
        dtg_series = {
            "name": str(columns[dtg_idx]) + " (-)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"color": COLORS["dtg"], "width": 1.5, "type": "dashed"},
            "itemStyle": {"color": COLORS["dtg"]},
            "data": dtg_data,
        }
        if peak_x is not None:
            dtg_series["markPoint"] = {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": COLORS["dtg"]},
                "label": {
                    "show": True,
                    "formatter": peak_label,
                    "position": "top",
                    "color": "#333333",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [peak_x, peak_y]}],
            }
        series.append(dtg_series)

    option = {
        "title": {
            "text": clean_name(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": [item["name"] for item in series],
            "left": "center",
            "bottom": 8,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 70, "right": 70, "top": 60, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": str(columns[x_idx]),
            "nameLocation": "middle",
            "nameGap": 32,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": str(columns[weight_idx]),
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
            },
            {
                "type": "value",
                "name": (str(columns[dtg_idx]) + " (-)") if dtg_idx is not None else "DTG (-)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }
    return option


def main():
    path = Path(DATA_FILE)
    figures = []
    excel = pd.ExcelFile(path)
    for sheet_name in excel.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet_name)
        option = option_for_sheet(sheet_name, frame)
        if option is not None:
            figures.append(
                {
                    "name": clean_name(sheet_name),
                    "option": option,
                    "width": 614,
                    "height": 442,
                    "dpi": 300,
                    "formats": ["png"],
                }
            )
    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
