import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip())


def find_column(columns, patterns, fallback):
    for pattern in patterns:
        for i, name in enumerate(columns):
            if re.search(pattern, str(name), re.I):
                return i
    return fallback


def nice_sheet_name(value):
    name = clean_name(value)
    return re.sub(r"[^A-Za-z0-9가-힣._-]+", "_", name).strip("_") or "plot"


def build_figure(sheet_name, df):
    columns = list(df.columns)
    x_idx = find_column(columns, [r"temperature", r"temp", r"온도"], 1)
    y1_idx = find_column(columns, [r"weight", r"무게", r"질량"], 2)
    y2_idx = find_column(columns, [r"d\.?\s*w", r"dtg", r"derivative", r"미분"], 3)

    x = pd.to_numeric(df.iloc[:, x_idx], errors="coerce").to_numpy(dtype=float)
    y1 = pd.to_numeric(df.iloc[:, y1_idx], errors="coerce").to_numpy(dtype=float)
    y2_raw = pd.to_numeric(df.iloc[:, y2_idx], errors="coerce").to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(y1) & np.isfinite(y2_raw)
    x, y1, y2_raw = x[valid], y1[valid], y2_raw[valid]
    if not len(x):
        return None

    order = np.argsort(x)
    x, y1, y2_raw = x[order], y1[order], y2_raw[order]
    y2 = -y2_raw

    residue_target = 800.0
    residue_idx = int(np.argmin(np.abs(x - residue_target)))
    residue_x, residue_y = float(x[residue_idx]), float(y1[residue_idx])

    peak_candidates = np.flatnonzero(x > 150)
    peak_idx = int(peak_candidates[np.argmax(y2[peak_candidates])]) if len(peak_candidates) else int(np.argmax(y2))
    peak_x, peak_y = float(x[peak_idx]), float(y2[peak_idx])

    x_label = str(columns[x_idx])
    y1_label = str(columns[y1_idx])
    y2_label = str(columns[y2_idx])

    option = {
        "title": {
            "text": clean_name(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [y1_label, y2_label], "left": "center", "top": 38},
        "grid": {"left": 72, "right": 76, "top": 92, "bottom": 66},
        "xAxis": {
            "type": "value",
            "name": x_label,
            "nameLocation": "middle",
            "nameGap": 34,
            "axisLine": {"lineStyle": {"color": "#555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": y1_label,
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisLabel": {"color": "#1f4e9c", "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"color": "#1f4e9c", "fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": y2_label + " (-)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisLine": {"show": True, "lineStyle": {"color": "green"}},
                "axisLabel": {"color": "green", "fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"color": "green", "fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": y1_label,
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "data": [[float(a), float(b)] for a, b in zip(x, y1)],
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_y:.1f}%",
                        "position": "right",
                        "fontFamily": "Noto Sans CJK KR",
                    },
                    "data": [{"coord": [residue_x, residue_y]}],
                },
            },
            {
                "name": y2_label,
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": [[float(a), float(b)] for a, b in zip(x, y2)],
                "lineStyle": {"color": "green", "width": 2},
                "itemStyle": {"color": "green"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "green"},
                    "label": {
                        "show": True,
                        "formatter": f"{peak_x:.0f} °C",
                        "position": "top",
                        "fontFamily": "Noto Sans CJK KR",
                    },
                    "data": [{"coord": [peak_x, peak_y]}],
                },
            },
        ],
        "animation": False,
    }

    return {
        "name": nice_sheet_name(sheet_name),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }


def main():
    path = Path(DATA_FILE)
    figures = []
    excel = pd.ExcelFile(path)
    for sheet in excel.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        figure = build_figure(sheet, df)
        if figure is not None:
            figures.append(figure)
    json.dump({"figures": figures}, sys.stdout, ensure_ascii=False, allow_nan=False)


if __name__ == "__main__":
    main()
