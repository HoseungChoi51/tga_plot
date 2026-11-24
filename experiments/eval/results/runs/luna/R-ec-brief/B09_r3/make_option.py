import json
import os
import re

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"


def clean_number(value):
    if pd.isna(value):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def main():
    book = pd.ExcelFile(DATA_FILE)
    sheet_name = next((s for s in book.sheet_names if s.strip().upper() == "PE"), None)
    if sheet_name is None:
        raise ValueError("PE sheet not found")

    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    cols = list(df.columns)

    def find_col(pattern, fallback_index):
        for col in cols:
            if re.search(pattern, str(col), re.IGNORECASE):
                return col
        return cols[fallback_index]

    x_col = find_col(r"temperature|temp", 1)
    weight_col = find_col(r"weight", 2)
    dtg_col = find_col(r"deriv|dtg", 3)

    data = pd.DataFrame({
        "x": pd.to_numeric(df[x_col], errors="coerce"),
        "weight": pd.to_numeric(df[weight_col], errors="coerce"),
        "dtg": pd.to_numeric(df[dtg_col], errors="coerce"),
    }).dropna()

    data = data.sort_values("x")
    x = data["x"].to_numpy(dtype=float)
    weight = data["weight"].to_numpy(dtype=float)
    dtg = data["dtg"].to_numpy(dtype=float)

    residue_index = int(np.argmin(np.abs(x - 800)))
    residue_x = float(x[residue_index])
    residue_y = float(weight[residue_index])

    peak_candidates = np.flatnonzero((x > 150) & (dtg < 0))
    if len(peak_candidates):
        peak_index = int(peak_candidates[np.argmin(dtg[peak_candidates])])
        peak_x = float(x[peak_index])
        peak_y = float(-dtg[peak_index])
    else:
        peak_x = None
        peak_y = None

    weight_data = [[float(a), float(b)] for a, b in zip(x, weight)]
    dtg_data = [[float(a), float(-b)] for a, b in zip(x, dtg)]

    mark_points = [{
        "name": f"Residue {residue_y:.1f}%",
        "coord": [residue_x, residue_y],
        "value": f"Residue {residue_y:.1f}%",
    }]
    if peak_x is not None:
        mark_points.append({
            "name": f"{peak_x:.0f} °C",
            "coord": [peak_x, peak_y],
            "value": f"{peak_x:.0f} °C",
        })

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Weight (%)", "DTG (-)"],
            "left": "center",
            "top": "bottom",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 72, "right": 72, "top": 60, "bottom": 66},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "min": 100,
            "max": 700,
            "interval": 100,
            "nameLocation": "middle",
            "nameGap": 38,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "position": "left",
                "nameLocation": "middle",
                "nameGap": 50,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            {
                "type": "value",
                "name": "DTG (-)",
                "position": "right",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "connectNulls": False,
                "lineStyle": {"color": "#ff0000", "width": 3},
                "itemStyle": {"color": "#ff0000"},
                "data": weight_data,
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 10,
                    "itemStyle": {"color": "#ff0000"},
                    "label": {
                        "show": True,
                        "position": "top",
                        "fontFamily": "Noto Sans CJK KR",
                    },
                    "data": mark_points,
                },
            },
            {
                "name": "DTG (-)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "connectNulls": False,
                "lineStyle": {"color": "#c0392b", "width": 1.5},
                "itemStyle": {"color": "#c0392b"},
                "data": dtg_data,
            },
        ],
    }

    figure = {
        "name": "PE",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }
    print(json.dumps({"figures": [figure]}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
