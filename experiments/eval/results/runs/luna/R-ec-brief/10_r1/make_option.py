import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

WEIGHT_COLOR = "#1f4e9c"
DTG_COLOR = "#c0392b"
FONT = "Noto Sans CJK KR"


def clean_name(value):
    name = re.sub(r"[^\w가-힣.-]+", "_", str(value).strip())
    return name.strip("_") or "plot"


def main():
    source = Path(DATA_FILE)
    figures = []

    workbook = pd.ExcelFile(source)
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(source, sheet_name=sheet_name)
        frame.columns = [str(col).strip() for col in frame.columns]

        def find_column(candidates, fallback_index):
            for col in frame.columns:
                if any(term in col.lower() for term in candidates):
                    return col
            return frame.columns[fallback_index]

        x_col = find_column(["temperature", "temp"], 1)
        weight_col = find_column(["weight", "mass"], 2)
        dtg_col = find_column(["d.w", "dtg", "derivative"], 3)

        data = frame[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        x = data[x_col].to_numpy(dtype=float)
        weight = data[weight_col].to_numpy(dtype=float)
        dtg = data[dtg_col].to_numpy(dtype=float)

        # Residue at the measured point nearest 700 °C.
        residue_index = int(np.argmin(np.abs(x - 700.0)))
        residue_x = float(x[residue_index])
        residue_y = float(weight[residue_index])

        # Highest positive DTG peak above 150 °C, plotted as -DTG so loss peaks point up.
        peak_candidates = np.flatnonzero(x > 150.0)
        if len(peak_candidates):
            peak_index = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
            peak_x = float(x[peak_index])
            peak_y = float(-dtg[peak_index])
        else:
            peak_index = int(np.argmax(-dtg))
            peak_x = float(x[peak_index])
            peak_y = float(-dtg[peak_index])

        option = {
            "animation": False,
            "backgroundColor": "#ffffff",
            "textStyle": {"fontFamily": FONT, "color": "#333333"},
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "top": 10,
                "textStyle": {"fontFamily": FONT, "fontSize": 16, "fontWeight": "normal"},
            },
            "legend": {
                "data": ["Weight (%)", "DTG (-D.W)"],
                "left": 18,
                "top": "middle",
                "orient": "vertical",
                "textStyle": {"fontFamily": FONT, "fontSize": 11},
            },
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 82, "right": 82, "top": 58, "bottom": 68},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": FONT},
                "splitLine": {"show": False},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "axisLine": {"show": True, "lineStyle": {"color": WEIGHT_COLOR}},
                    "axisLabel": {"fontFamily": FONT, "color": WEIGHT_COLOR},
                    "nameTextStyle": {"color": WEIGHT_COLOR, "fontFamily": FONT},
                    "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLine": {"show": True, "lineStyle": {"color": DTG_COLOR}},
                    "axisLabel": {"fontFamily": FONT, "color": DTG_COLOR},
                    "nameTextStyle": {"color": DTG_COLOR, "fontFamily": FONT},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "yAxisIndex": 0,
                    "data": [[float(a), float(b)] for a, b in zip(x, weight)],
                    "showSymbol": False,
                    "symbol": "circle",
                    "lineStyle": {"width": 2, "color": WEIGHT_COLOR},
                    "itemStyle": {"color": WEIGHT_COLOR},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "data": [
                            {
                                "coord": [residue_x, residue_y],
                                "value": residue_y,
                                "itemStyle": {"color": WEIGHT_COLOR},
                                "label": {
                                    "show": True,
                                    "formatter": f"Residue {residue_y:.2f}%",
                                    "position": "right",
                                    "color": WEIGHT_COLOR,
                                    "fontFamily": FONT,
                                },
                            }
                        ],
                    },
                },
                {
                    "name": "DTG (-D.W)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": [[float(a), float(-b)] for a, b in zip(x, dtg)],
                    "showSymbol": False,
                    "lineStyle": {"width": 2, "color": DTG_COLOR},
                    "itemStyle": {"color": DTG_COLOR},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "data": [
                            {
                                "coord": [peak_x, peak_y],
                                "value": peak_y,
                                "itemStyle": {"color": DTG_COLOR},
                                "label": {
                                    "show": True,
                                    "formatter": f"{peak_x:.0f} °C",
                                    "position": "top",
                                    "color": DTG_COLOR,
                                    "fontFamily": FONT,
                                },
                            }
                        ],
                    },
                },
            ],
        }

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
