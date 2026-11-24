import json
import os

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

figures = []
colors = ["#5470C6", "#91CC75", "#FAC858"]

for index, sheet_name in enumerate(pd.ExcelFile(DATA_FILE).sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
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
        (column for column in df.columns if "d.w" in column.lower() or "dw" in column.lower()),
        df.columns[3],
    )

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    derivative = pd.to_numeric(df[derivative_col], errors="coerce")
    valid = temperature.notna()

    temp_values = temperature[valid].tolist()
    weight_values = [
        [float(x), None if pd.isna(y) else float(y)]
        for x, y in zip(temperature[valid], weight[valid])
    ]
    derivative_values = [
        [float(x), None if pd.isna(y) else float(y)]
        for x, y in zip(temperature[valid], derivative[valid])
    ]

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "title": {
            "text": sheet_name,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 34, "data": ["Weight (%)", "D.W (%/°C)"]},
        "grid": {"left": 70, "right": 75, "top": 78, "bottom": 65},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": float(temperature[valid].max()),
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
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
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "scale": True,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "showSymbol": False,
                "connectNulls": False,
                "data": weight_values,
                "lineStyle": {"width": 2, "color": colors[index % len(colors)]},
                "markArea": {
                    "silent": True,
                    "itemStyle": {"color": "rgba(180, 180, 180, 0.28)"},
                    "data": [[{"xAxis": 300}, {"xAxis": 450}]],
                },
            },
            {
                "name": "D.W (%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "connectNulls": False,
                "data": derivative_values,
                "lineStyle": {"width": 1.5, "color": "#EE6666"},
            },
        ],
    }

    safe_name = "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in sheet_name
    )
    figures.append(
        {
            "name": safe_name or f"plot{index + 1}",
            "option": option,
            "width": 900,
            "height": 560,
            "dpi": 300,
            "formats": ["png"],
        }
    )

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
