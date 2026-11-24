import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"


def main():
    df = pd.read_excel(DATA_FILE, sheet_name="PET", engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    temp_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)
    deriv_col = next(c for c in df.columns if "Deriv" in c)

    temp = pd.to_numeric(df[temp_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    deriv = pd.to_numeric(df[deriv_col], errors="coerce")
    valid = temp.notna() & weight.notna() & deriv.notna()
    temp, weight, deriv = temp[valid], weight[valid], deriv[valid]

    residual = float(weight.iloc[-1])
    option = {
        "animation": False,
        "title": {
            "text": "PET 열분해",
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "left": 18,
            "bottom": 12,
            "orient": "horizontal",
            "data": ["Weight (%)", "Deriv. Weight (%/°C)"],
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 72, "right": 76, "top": 60, "bottom": 75, "containLabel": True},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": float(temp.min()),
            "max": float(temp.max()),
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#d9d9d9", "type": "dashed"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": 0,
                "max": 105,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#d9d9d9", "type": "dashed"}},
            },
            {
                "type": "value",
                "name": "Deriv. Weight (%/°C)",
                "nameLocation": "middle",
                "nameGap": 55,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 2, "color": "#2468a2"},
                "data": [[float(x), float(y)] for x, y in zip(temp, weight)],
            },
            {
                "name": "Deriv. Weight (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "symbol": "none",
                "lineStyle": {"width": 1.7, "color": "#d9534f"},
                "data": [[float(x), float(y)] for x, y in zip(temp, deriv)],
            },
        ],
        "graphic": [
            {
                "type": "text",
                "right": 18,
                "top": 43,
                "style": {
                    "text": f"잔류량: {residual:.2f}%",
                    "font": "14px Noto Sans CJK KR",
                    "fill": "#333",
                },
            }
        ],
    }

    result = {
        "figures": [
            {
                "name": "PET_열분해",
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
