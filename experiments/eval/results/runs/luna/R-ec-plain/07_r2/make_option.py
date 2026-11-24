import json
from pathlib import Path

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

colors = ["#3569a8", "#d66b3d", "#438c69"]
figures = []

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for index, (sheet_name, df) in enumerate(sheets.items()):
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(
        (column for column in df.columns if "temperature" in column.lower()),
        df.columns[1],
    )
    weight_col = next(
        (column for column in df.columns if "weight" in column.lower()),
        df.columns[2],
    )
    derivative_col = next(
        (column for column in df.columns if "d.w" in column.lower() or "derivative" in column.lower()),
        df.columns[3] if len(df.columns) > 3 else None,
    )

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid_weight = temperature.notna() & weight.notna()

    series = [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 0,
            "lineStyle": {"width": 2, "color": colors[index % len(colors)]},
            "data": [
                [float(x), float(y)]
                for x, y in zip(temperature[valid_weight], weight[valid_weight])
            ],
        }
    ]

    y_axes = [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontSize": 11},
            "nameTextStyle": {"fontSize": 12},
        }
    ]

    if derivative_col is not None:
        derivative = pd.to_numeric(df[derivative_col], errors="coerce")
        valid_derivative = temperature.notna() & derivative.notna()
        series.append(
            {
                "name": "Derivative",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {"width": 1.5, "color": "#777777"},
                "data": [
                    [float(x), float(y)]
                    for x, y in zip(
                        temperature[valid_derivative], derivative[valid_derivative]
                    )
                ],
            }
        )
        y_axes.append(
            {
                "type": "value",
                "name": "D.W. (%/°C)",
                "nameLocation": "middle",
                "nameGap": 55,
                "axisLabel": {"fontSize": 11},
                "nameTextStyle": {"fontSize": 12},
                "splitLine": {"show": False},
            }
        )

    option = {
        "animation": False,
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 12,
            "textStyle": {"fontSize": 16, "fontWeight": "normal"},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "top": 12,
            "right": 18,
            "textStyle": {"fontSize": 9},
            "data": [item["name"] for item in series],
        },
        "grid": {"left": 82, "right": 82 if len(y_axes) > 1 else 30, "top": 60, "bottom": 58},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "axisLabel": {"fontSize": 11},
            "nameTextStyle": {"fontSize": 12},
            "splitLine": {"lineStyle": {"color": "#e5e5e5"}},
        },
        "yAxis": y_axes,
        "series": series,
    }

    figures.append(
        {
            "name": f"tga_{index + 1}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
