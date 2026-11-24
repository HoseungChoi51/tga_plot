import json
import os
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"


def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        x_col = next((c for c in df.columns if "temperature" in c.lower()), None)
        weight_col = next((c for c in df.columns if "weight (%)" in c.lower()), None)
        heat_col = next((c for c in df.columns if "heat flow" in c.lower()), None)

        if not (x_col and weight_col and heat_col):
            continue

        data = df[[x_col, weight_col, heat_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        x = data[x_col].to_numpy(dtype=float)
        weight = data[weight_col].to_numpy(dtype=float)
        heat = data[heat_col].to_numpy(dtype=float)

        residue_idx = int(np.argmin(np.abs(x - 800.0)))
        residue_x = float(x[residue_idx])
        residue_y = float(weight[residue_idx])
        residue_text = f"Residue {residue_y:.1f}%"

        option = {
            "animation": False,
            "title": {
                "text": sheet_name,
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Weight", "Heat Flow"],
                "left": "center",
                "top": 36,
            },
            "grid": {"left": 75, "right": 75, "top": 90, "bottom": 65},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": float(np.nanmin(x)),
                "max": float(np.nanmax(x)),
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
                {
                    "type": "value",
                    "name": "Heat flow (W/g)",
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
            ],
            "series": [
                {
                    "name": "Weight",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "itemStyle": {"color": "#1f4e9c"},
                    "data": [[float(a), float(b)] for a, b in zip(x, weight)],
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": residue_text,
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                        },
                        "data": [{"coord": [residue_x, residue_y]}],
                    },
                },
                {
                    "name": "Heat Flow",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "lineStyle": {"color": "#c0392b", "width": 2},
                    "itemStyle": {"color": "#c0392b"},
                    "data": [[float(a), float(b)] for a, b in zip(x, heat)],
                },
            ],
        }

        figures.append(
            {
                "name": f"plot_{sheet_name}",
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
