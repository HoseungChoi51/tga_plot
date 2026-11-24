import json
from pathlib import Path

import pandas as pd


DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]


def read_data(path):
    # CSV and text inputs in this dataset are comma-delimited.
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [str(c).strip() for c in df.columns]

    x_col = next(c for c in df.columns if "Temperature" in c)
    y_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

    df[x_col] = pd.to_numeric(df[x_col], errors="coerce")
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df = df.dropna(subset=[x_col, y_col]).sort_values(x_col)
    return [[float(x), float(y)] for x, y in zip(df[x_col], df[y_col])]


series = []
for path, label, color in zip(
    DATA_FILES,
    ["Lot A", "Lot B"],
    ["#5470C6", "#EE6666"],
):
    series.append(
        {
            "name": label,
            "type": "line",
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": color},
            "itemStyle": {"color": color},
            "data": read_data(path),
        }
    )

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["Lot A", "Lot B"],
        "top": 10,
    },
    "grid": {
        "left": 78,
        "right": 28,
        "top": 58,
        "bottom": 62,
        "containLabel": False,
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#333"},
        "splitLine": {"lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"color": "#333"},
        "splitLine": {"lineStyle": {"color": "#e5e5e5"}},
    },
    "series": series,
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "lot_weight_comparison",
                    "option": option,
                    "width": 614,
                    "height": 442,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
