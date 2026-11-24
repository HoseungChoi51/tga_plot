import json
import math
import re
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"


def clean_number(value):
    if pd.isna(value):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def main():
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)

    # Columns B, C, and D: Temperature, Weight(%), and Deriv.Weight.
    x = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")
    deriv = pd.to_numeric(df.iloc[:, 3], errors="coerce")
    valid = x.notna() & weight.notna() & deriv.notna()

    x = x[valid].to_numpy(dtype=float)
    weight = weight[valid].to_numpy(dtype=float)
    deriv = deriv[valid].to_numpy(dtype=float)

    if not len(x):
        raise ValueError(f"No valid data found in sheet {SHEET_NAME!r}")

    # The displayed DTG curve is inverted so mass-loss peaks point upward.
    displayed_deriv = -deriv
    peak_index = int(np.argmax(displayed_deriv))
    residue_index = int(np.argmin(np.abs(x - 800.0)))

    x_min = min(0.0, float(np.floor(np.min(x) / 200.0) * 200.0))
    x_max = float(np.ceil(np.max(x) / 200.0) * 200.0)
    if x_max <= x_min:
        x_max = x_min + 200.0

    # Use 20-unit weight ticks and 0.2-unit DTG ticks.
    weight_min = float(np.floor(np.min(weight) / 20.0) * 20.0)
    weight_max = float(np.ceil(np.max(weight) / 20.0) * 20.0)
    if weight_max <= weight_min:
        weight_max = weight_min + 20.0

    dtg_min = float(np.floor(np.min(displayed_deriv) / 0.2) * 0.2)
    dtg_max = float(np.ceil(np.max(displayed_deriv) / 0.2) * 0.2)
    if dtg_max <= dtg_min:
        dtg_max = dtg_min + 0.2

    def pairs(xs, ys):
        return [
            [clean_number(a), clean_number(b)]
            for a, b in zip(xs, ys)
            if clean_number(a) is not None and clean_number(b) is not None
        ]

    option = {
        "animation": False,
        "title": {
            "text": SHEET_NAME,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Weight(%)", "Deriv.Weight"],
            "left": "center",
            "bottom": 8,
        },
        "grid": {"left": 76, "right": 76, "top": 72, "bottom": 76},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 36,
            "min": x_min,
            "max": x_max,
            "interval": 200,
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": weight_min,
                "max": weight_max,
                "interval": 20,
                "axisLabel": {"formatter": "{value}"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
            },
            {
                "type": "value",
                "name": "Deriv.Weight (-D.W, %/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": dtg_min,
                "max": dtg_max,
                "interval": 0.2,
                "axisLabel": {
                    "formatter": "{value}",
                    "margin": 10,
                },
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight(%)",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "lineStyle": {"width": 2, "color": "#1f4e9c"},
                "data": pairs(x, weight),
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "data": [
                        {
                            "coord": [
                                clean_number(x[residue_index]),
                                clean_number(weight[residue_index]),
                            ],
                            "label": {
                                "show": True,
                                "formatter": f"Residue {weight[residue_index]:.1f}%",
                                "position": "top",
                                "color": "#1f4e9c",
                            },
                        }
                    ],
                },
            },
            {
                "name": "Deriv.Weight",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {"width": 2, "color": "#c0392b"},
                "data": pairs(x, displayed_deriv),
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#c0392b"},
                    "data": [
                        {
                            "coord": [
                                clean_number(x[peak_index]),
                                clean_number(displayed_deriv[peak_index]),
                            ],
                            "label": {
                                "show": True,
                                "formatter": (
                                    f"Max {displayed_deriv[peak_index]:.3g} "
                                    f"at {x[peak_index]:.0f} °C"
                                ),
                                "position": "top",
                                "color": "#c0392b",
                            },
                        }
                    ],
                },
            },
        ],
    }

    result = {
        "figures": [
            {
                "name": "1006R1-V_normal",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        ]
    }
    json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
