import json
import os
import re
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_name(value):
    name = re.sub(r"[^\w.-]+", "_", str(value).strip(), flags=re.UNICODE).strip("_")
    return name or "plot"


def make_option(sheet_name, temp, weight, dtg):
    valid = np.isfinite(temp) & np.isfinite(weight) & np.isfinite(dtg)
    temp, weight, dtg = temp[valid], weight[valid], dtg[valid]
    if not len(temp):
        return None

    order = np.argsort(temp)
    temp, weight, dtg = temp[order], weight[order], dtg[order]

    weight_data = [[float(x), float(y)] for x, y in zip(temp, weight)]
    dtg_data = [[float(x), float(-y)] for x, y in zip(temp, dtg)]

    residue_idx = int(np.argmin(np.abs(temp - 800.0)))
    residue_x = float(temp[residue_idx])
    residue_y = float(weight[residue_idx])

    peak_mask = temp > 150.0
    if np.any(peak_mask):
        peak_candidates = np.flatnonzero(peak_mask)
        peak_idx = int(peak_candidates[np.argmax(-dtg[peak_mask])])
        peak_x = float(temp[peak_idx])
        peak_y = float(-dtg[peak_idx])
        peak_label = f"{peak_x:.0f} °C"
        peak_point = {"coord": [peak_x, peak_y], "value": [peak_x, peak_y]}
    else:
        peak_label = ""
        peak_point = None

    y2_min = -0.05
    y2_max = 1.2

    series = [
        {
            "name": "Weight",
            "type": "line",
            "data": weight_data,
            "showSymbol": False,
            "yAxisIndex": 0,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_y:.1f}%",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [residue_x, residue_y], "value": [residue_x, residue_y]}],
            },
        },
        {
            "name": "DTG",
            "type": "line",
            "data": dtg_data,
            "showSymbol": False,
            "yAxisIndex": 1,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
        },
    ]

    if peak_point is not None:
        series[1]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": peak_label,
                "position": "top",
                "color": "#c0392b",
                "fontFamily": "Noto Sans CJK KR",
            },
            "data": [peak_point],
        }

    return {
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "animation": False,
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Weight", "DTG"],
            "left": "center",
            "top": "bottom",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 72, "right": 72, "top": 58, "bottom": 76},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": float(np.nanmin(temp)),
            "max": float(np.nanmax(temp)),
            "interval": 100,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "position": "right",
                "min": y2_min,
                "max": y2_max,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }


def main():
    path = DATA_FILE
    if not os.path.isfile(path):
        print(json.dumps({"figures": []}, ensure_ascii=False))
        return

    workbook = pd.ExcelFile(path)
    figures = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name)
        normalized = {str(c).strip().lower(): c for c in df.columns}

        def find_column(predicate, fallback_index):
            for normalized_name, original in normalized.items():
                if predicate(normalized_name):
                    return original
            return df.columns[fallback_index] if len(df.columns) > fallback_index else None

        temp_col = find_column(lambda s: "temp" in s or "온도" in s, 1)
        weight_col = find_column(lambda s: "weight" in s or "wt" in s or "무게" in s, 2)
        dtg_col = find_column(lambda s: "dtg" in s or "d.w" in s or "derivative" in s, 3)

        if temp_col is None or weight_col is None or dtg_col is None:
            continue

        temp = pd.to_numeric(df[temp_col], errors="coerce").to_numpy(dtype=float)
        weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
        dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)

        option = make_option(sheet_name, temp, weight, dtg)
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
