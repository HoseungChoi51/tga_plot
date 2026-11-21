import json
import math
import os

import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"


def finite_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


df = pd.read_excel(DATA_FILE, sheet_name=1, engine="openpyxl")
df.columns = [str(column).strip() for column in df.columns]

temperature_col = next(
    (col for col in df.columns if "temperature" in col.lower()),
    df.columns[1],
)
weight_col = next(
    (col for col in df.columns if "weight" in col.lower() and "deriv" not in col.lower()),
    df.columns[2],
)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid]
weight = weight[valid]

points = [
    [finite_number(t), finite_number(w)]
    for t, w in zip(temperature, weight)
    if finite_number(t) is not None and finite_number(w) is not None
]
points.sort(key=lambda point: point[0])


def weight_at(target):
    # Interpolate the measured curve at the requested temperature.
    return finite_number(
        pd.Series(
            weight.to_numpy(),
            index=temperature.to_numpy(),
        )
        .groupby(level=0)
        .mean()
        .sort_index()
        .reindex(
            pd.Index(
                sorted(set(temperature.to_numpy()).union({float(target)})),
                dtype=float,
            )
        )
        .interpolate(method="index")
        .loc[float(target)]
    )


markers = []
for target in (300, 600):
    value = weight_at(target)
    if value is not None:
        markers.append(
            {
                "coord": [target, value],
                "value": value,
                "label": {
                    "show": True,
                    "formatter": f"{target} °C: {value:.2f}%",
                    "position": "top",
                    "distance": 9,
                    "color": "#222",
                    "fontSize": 12,
                    "fontFamily": "Noto Sans CJK KR",
                },
                "itemStyle": {"color": "#d62728"},
            }
        )

option = {
    "animation": False,
    "title": {
        "text": "PVC TGA",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": "{value}%",
    },
    "grid": {"left": 78, "right": 30, "top": 65, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#e5e5e5"}},
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": points,
            "showSymbol": False,
            "symbol": "circle",
            "lineStyle": {"width": 2, "color": "#2878b5"},
            "itemStyle": {"color": "#2878b5"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 10,
                "data": markers,
            },
        }
    ],
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "pvc_tga",
                    "option": option,
                    "width": 900,
                    "height": 560,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
