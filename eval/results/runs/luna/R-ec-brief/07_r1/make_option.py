import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_name(value, fallback):
    text = str(value).strip() if value is not None else ""
    return text or fallback


def find_column(columns, terms, fallback_index):
    for i, name in enumerate(columns):
        n = str(name).lower()
        if any(term in n for term in terms):
            return i
    return min(fallback_index, len(columns) - 1)


def json_safe(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def main():
    figures = []
    book = pd.ExcelFile(DATA_FILE)

    for sheet_name in book.sheet_names:
        df = pd.read_excel(book, sheet_name=sheet_name)
        if df.empty or len(df.columns) < 2:
            continue

        x_idx = find_column(df.columns, ("temperature", "temp", "온도"), 1 if len(df.columns) > 2 else 0)
        y1_idx = find_column(df.columns, ("weight", "mass", "중량", "무게"), 2 if len(df.columns) > 2 else 1)
        y2_idx = find_column(df.columns, ("d.w", "dtg", "derivative", "미분"), 3 if len(df.columns) > 3 else len(df.columns) - 1)

        x_name = clean_name(df.columns[x_idx], "Temperature")
        y1_name = clean_name(df.columns[y1_idx], "Weight (%)")
        y2_name = clean_name(df.columns[y2_idx], "DTG (%/°C)")

        x = pd.to_numeric(df.iloc[:, x_idx], errors="coerce")
        y1 = pd.to_numeric(df.iloc[:, y1_idx], errors="coerce")
        y2 = pd.to_numeric(df.iloc[:, y2_idx], errors="coerce")
        valid = x.notna() & y1.notna() & y2.notna()
        x = x[valid].to_numpy(dtype=float)
        y1 = y1[valid].to_numpy(dtype=float)
        y2 = y2[valid].to_numpy(dtype=float)
        if len(x) == 0:
            continue

        order = np.argsort(x)
        x, y1, y2 = x[order], y1[order], y2[order]
        negated_dtg = -y2

        residue_idx = int(np.argmin(np.abs(x - 800.0)))
        residue_temp = float(x[residue_idx])
        residue = float(y1[residue_idx])

        peak_candidates = np.flatnonzero(x > 150.0)
        if len(peak_candidates):
            peak_idx = int(peak_candidates[np.argmax(negated_dtg[peak_candidates])])
        else:
            peak_idx = int(np.argmax(negated_dtg))
        peak_temp = float(x[peak_idx])
        peak_value = float(negated_dtg[peak_idx])

        option = {
            "animation": False,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": [y1_name, y2_name],
                "top": 10,
                "right": 12,
                "orient": "vertical",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 9},
            },
            "grid": {"left": 65, "right": 65, "top": 62, "bottom": 58},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 34,
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": y1_name,
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                    "axisLabel": {"color": "#1f4e9c", "fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"color": "#1f4e9c", "fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                    "axisLabel": {"color": "#c0392b", "fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"color": "#c0392b", "fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": y1_name,
                    "type": "line",
                    "yAxisIndex": 0,
                    "showSymbol": False,
                    "data": [[json_safe(a), json_safe(b)] for a, b in zip(x, y1)],
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue:.1f}%",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                        },
                        "data": [{"coord": [residue_temp, residue]}],
                    },
                },
                {
                    "name": y2_name,
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "data": [[json_safe(a), json_safe(b)] for a, b in zip(x, negated_dtg)],
                    "lineStyle": {"color": "#c0392b", "width": 2},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": f"{peak_temp:.0f} °C",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                        },
                        "data": [{"coord": [peak_temp, peak_value]}],
                    },
                },
            ],
        }

        safe_sheet = re.sub(r"[^A-Za-z0-9_-]+", "_", str(sheet_name)).strip("_") or "plot"
        figures.append(
            {
                "name": safe_sheet,
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
