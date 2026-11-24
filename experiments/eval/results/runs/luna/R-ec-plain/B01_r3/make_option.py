import json
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

mask = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[mask].to_numpy()
weight = weight[mask].to_numpy()
derivative = derivative[mask].to_numpy()

# Highlight each mass-loss interval with a separate, translucent area.
intervals = [
    (120, 250, "H2O", "rgba(76, 175, 80, 0.14)"),
    (430, 580, "CO", "rgba(255, 152, 0, 0.14)"),
    (640, 830, "CO2", "rgba(33, 150, 243, 0.14)"),
]

series = [
    {
        "name": "Weight (%)",
        "type": "line",
        "yAxisIndex": 0,
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": "#333333"},
        "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
        "markArea": {
            "silent": True,
            "label": {"show": False},
            "data": [
                [
                    {"xAxis": start, "itemStyle": {"color": color}},
                    {"xAxis": end},
                ]
                for start, end, _, color in intervals
            ],
        },
    },
    {
        "name": "Deriv. Weight (%/°C)",
        "type": "line",
        "yAxisIndex": 1,
        "showSymbol": False,
        "lineStyle": {"width": 1.5, "color": "#b23a48"},
        "data": [[float(x), float(y)] for x, y in zip(temperature, derivative)],
    },
]

# Put gas labels above the shaded temperature spans.
for start, end, label, color in intervals:
    series.append(
        {
            "name": label,
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [],
            "silent": True,
            "markPoint": {
                "symbol": "none",
                "label": {
                    "show": True,
                    "formatter": label,
                    "position": "top",
                    "color": "#222222",
                    "fontSize": 13,
                    "fontWeight": "bold",
                },
                "data": [
                    {
                        "coord": [(start + end) / 2, 101.0],
                        "itemStyle": {"color": color},
                    }
                ],
            },
        }
    )

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight (%)", "Deriv. Weight (%/°C)"], "top": 8},
    "grid": {"left": 75, "right": 75, "top": 55, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 950,
        "axisLine": {"lineStyle": {"color": "#555555"}},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 35,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "splitLine": {"lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "Deriv. Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLabel": {"color": "#b23a48"},
            "nameTextStyle": {"color": "#b23a48"},
            "axisLine": {"show": True, "lineStyle": {"color": "#b23a48"}},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "caox_mass_loss",
                    "option": option,
                    "width": 900,
                    "height": 600,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
