import json
import os
import sys

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"


def main():
    df = pd.read_csv(DATA_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    dtg_col = "Deriv. Weight (%/°C)"

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()

    data = [
        [float(a), float(b), float(c)]
        for a, b, c in zip(x[valid], weight[valid], dtg[valid])
    ]

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "textStyle": {
            "fontFamily": "Noto Sans CJK KR, sans-serif",
            "color": "#222222",
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "line"},
        },
        "axisPointer": {"link": [{"xAxisIndex": [0, 1]}]},
        "grid": [
            {"left": 82, "right": 30, "top": 55, "height": "34%"},
            {"left": 82, "right": 30, "top": "57%", "bottom": 72},
        ],
        "xAxis": [
            {
                "type": "value",
                "gridIndex": 0,
                "min": 30,
                "max": 950,
                "axisLabel": {"show": False},
                "axisLine": {"lineStyle": {"color": "#666666"}},
                "axisTick": {"show": True},
                "splitLine": {"show": False},
            },
            {
                "type": "value",
                "gridIndex": 1,
                "min": 30,
                "max": 950,
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLine": {"lineStyle": {"color": "#666666"}},
                "axisLabel": {"color": "#333333"},
                "axisTick": {"show": True},
                "splitLine": {"show": False},
            },
        ],
        "yAxis": [
            {
                "type": "value",
                "gridIndex": 0,
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 54,
                "min": 35,
                "max": 102,
                "axisLine": {"show": True, "lineStyle": {"color": "#666666"}},
                "axisLabel": {"color": "#333333"},
                "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
            },
            {
                "type": "value",
                "gridIndex": 1,
                "name": "DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 58,
                "axisLine": {"show": True, "lineStyle": {"color": "#666666"}},
                "axisLabel": {"color": "#333333"},
                "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "xAxisIndex": 0,
                "yAxisIndex": 0,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.8, "color": "#2563a6"},
                "data": [[row[0], row[1]] for row in data],
            },
            {
                "name": "DTG (%/°C)",
                "type": "line",
                "xAxisIndex": 1,
                "yAxisIndex": 1,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.6, "color": "#c23b32"},
                "data": [[row[0], row[2]] for row in data],
            },
        ],
    }

    result = {
        "figures": [
            {
                "name": "tga_weight_dtg",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        ]
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
