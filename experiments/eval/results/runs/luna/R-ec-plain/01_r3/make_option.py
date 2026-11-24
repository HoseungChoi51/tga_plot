import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_sheet_name(name):
    name = re.sub(r"[^\w가-힣-]+", "_", str(name), flags=re.UNICODE).strip("_")
    return name or "plot"


def main():
    path = Path(DATA_FILE)
    figures = []

    workbook = pd.ExcelFile(path)
    colors = ["#2563eb", "#dc2626", "#16a34a"]

    for index, sheet in enumerate(workbook.sheet_names):
        df = pd.read_excel(path, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]

        temperature_col = next((c for c in df.columns if "temperature" in c.lower()), None)
        weight_col = next((c for c in df.columns if "weight" in c.lower()), None)
        derivative_col = next(
            (c for c in df.columns if "d.w" in c.lower() or "derivative" in c.lower()),
            None,
        )
        if temperature_col is None or weight_col is None or derivative_col is None:
            continue

        x = pd.to_numeric(df[temperature_col], errors="coerce")
        weight = pd.to_numeric(df[weight_col], errors="coerce")
        derivative = pd.to_numeric(df[derivative_col], errors="coerce")
        valid = x.notna() & weight.notna() & derivative.notna()
        x, weight, derivative = x[valid], weight[valid], derivative[valid]

        # Retain the full measured curve while keeping the JSON compact.
        stride = max(1, int(np.ceil(len(x) / 1800)))
        indices = list(range(0, len(x), stride))
        if len(x) and indices[-1] != len(x) - 1:
            indices.append(len(x) - 1)

        weight_data = [[round(float(x.iloc[i]), 4), round(float(weight.iloc[i]), 5)] for i in indices]
        derivative_data = [
            [round(float(x.iloc[i]), 4), round(float(derivative.iloc[i]), 6)] for i in indices
        ]

        figures.append(
            {
                "name": clean_sheet_name(sheet),
                "option": {
                    "animation": False,
                    "backgroundColor": "#ffffff",
                    "textStyle": {
                        "fontFamily": "Noto Sans CJK KR, sans-serif",
                        "color": "#263238",
                    },
                    "title": {
                        "text": f"TGA / DTG — {sheet}",
                        "left": "center",
                        "top": 12,
                        "textStyle": {"fontSize": 17, "fontWeight": "bold"},
                    },
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "cross"},
                        "valueFormatter": "{value}",
                    },
                    "legend": {
                        "top": 42,
                        "data": ["Weight (%)", "D.W (%/°C)"],
                    },
                    "grid": {"left": 78, "right": 78, "top": 86, "bottom": 65},
                    "xAxis": {
                        "type": "value",
                        "name": "Temperature (°C)",
                        "nameLocation": "middle",
                        "nameGap": 38,
                        "min": float(x.min()),
                        "max": float(x.max()),
                        "axisLine": {"lineStyle": {"color": "#667085"}},
                        "splitLine": {"lineStyle": {"color": "#e8edf2"}},
                    },
                    "yAxis": [
                        {
                            "type": "value",
                            "name": "Weight (%)",
                            "nameLocation": "middle",
                            "nameGap": 52,
                            "min": 0,
                            "max": 105,
                            "axisLine": {"show": True, "lineStyle": {"color": colors[index % 3]}},
                            "axisLabel": {"color": colors[index % 3]},
                            "splitLine": {"lineStyle": {"color": "#e8edf2"}},
                        },
                        {
                            "type": "value",
                            "name": "D.W (%/°C)",
                            "nameLocation": "middle",
                            "nameGap": 56,
                            "axisLine": {"show": True, "lineStyle": {"color": "#d97706"}},
                            "axisLabel": {"color": "#d97706"},
                            "splitLine": {"show": False},
                        },
                    ],
                    "series": [
                        {
                            "name": "Weight (%)",
                            "type": "line",
                            "yAxisIndex": 0,
                            "data": weight_data,
                            "showSymbol": False,
                            "smooth": False,
                            "lineStyle": {"width": 2.2, "color": colors[index % 3]},
                            "emphasis": {"focus": "series"},
                        },
                        {
                            "name": "D.W (%/°C)",
                            "type": "line",
                            "yAxisIndex": 1,
                            "data": derivative_data,
                            "showSymbol": False,
                            "smooth": False,
                            "lineStyle": {"width": 1.8, "color": "#d97706"},
                            "emphasis": {"focus": "series"},
                        },
                    ],
                },
                "width": 900,
                "height": 560,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
