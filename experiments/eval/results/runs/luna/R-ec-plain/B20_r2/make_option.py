import json
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
SHEET_NAME = "Acid-washed"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

x_col = next(c for c in df.columns if "Temperature" in c)
y_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)
dy_col = next(c for c in df.columns if "Deriv" in c)

x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[y_col], errors="coerce").to_numpy()
deriv = pd.to_numeric(df[dy_col], errors="coerce").to_numpy()
valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(deriv)

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#222"},
    "title": {
        "text": "Acid-washed TGA",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 17, "fontWeight": "bold"},
    },
    "legend": {"top": 42, "data": ["Weight", "Derivative weight"]},
    "grid": {"left": 78, "right": 82, "top": 88, "bottom": 68},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "interval": 100,
        "minorTick": {"show": True, "splitNumber": 5, "length": 3},
        "minorSplitLine": {"show": False},
        "axisTick": {"show": True},
        "axisLabel": {"fontSize": 11},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#4267a5"}},
            "axisLabel": {"color": "#4267a5"},
            "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}},
        },
        {
            "type": "value",
            "name": "Derivative weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 54,
            "inverse": True,
            "axisLine": {"show": True, "lineStyle": {"color": "#c4514a"}},
            "axisLabel": {"color": "#c4514a"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#4267a5"},
            "data": [[float(a), float(b)] for a, b in zip(x[valid], weight[valid])],
        },
        {
            "name": "Derivative weight",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 1.6, "color": "#c4514a"},
            "data": [[float(a), float(b)] for a, b in zip(x[valid], deriv[valid])],
        },
    ],
}

result = {
    "figures": [
        {
            "name": "acid_washed_tga",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}
json.dump(result, sys.stdout, ensure_ascii=False, allow_nan=False)
