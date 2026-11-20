import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

colors = ["#1f77b4", "#d62728", "#2ca02c"]
figures = []

for sheet_name, color in zip(
    ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"], colors
):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = next(c for c in df.columns if "temperature" in c.lower())
    weight_col = next(c for c in df.columns if "weight" in c.lower())
    derivative_col = next(
        c for c in df.columns
        if "d.w" in c.lower() or "dw" in c.lower() or "derivative" in c.lower()
    )

    data = df[[x_col, weight_col, derivative_col]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    x = data[x_col].tolist()
    weight = data[weight_col].tolist()
    derivative = data[derivative_col].tolist()

    figures.append({
        "name": sheet_name.replace(" ", "_"),
        "option": {
            "animation": False,
            "title": {
                "text": sheet_name,
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Weight (%)", "D.W (%/°C)"],
                "top": 32,
                "textStyle": {"fontFamily": "Noto Sans CJK KR"}
            },
            "grid": {"left": 68, "right": 68, "top": 78, "bottom": 58},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 34,
                "min": 30,
                "max": 900 if "750C" not in sheet_name else 750,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
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
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
                },
                {
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "data": [[a, b] for a, b in zip(x, weight)],
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "lineStyle": {"width": 2, "color": color}
                },
                {
                    "name": "D.W (%/°C)",
                    "type": "line",
                    "data": [[a, b] for a, b in zip(x, derivative)],
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "lineStyle": {"width": 1.5, "color": "#555555"}
                }
            ]
        },
        "width": 768,
        "height": 480,
        "dpi": 600,
        "formats": ["png"]
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
