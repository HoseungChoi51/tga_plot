import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PE")
temperature_c = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid_weight = temperature_c.notna() & weight.notna()
valid_derivative = temperature_c.notna() & derivative.notna()

temperature_k_weight = (temperature_c[valid_weight] + 273.15).tolist()
weight_data = weight[valid_weight].tolist()

# Convert derivative from %/°C to %/K (numerically identical), with temperature in K.
temperature_k_derivative = (temperature_c[valid_derivative] + 273.15).tolist()
derivative_data = derivative[valid_derivative].tolist()

option = {
    "animation": False,
    "title": {
        "text": "PE TGA",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight (%)", "Deriv. Weight (%/K)"], "top": 32},
    "grid": {"left": 75, "right": 78, "top": 80, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (K)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 303.15,
        "max": 1173.15,
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
            "name": "Deriv. Weight (%/K)",
            "nameLocation": "middle",
            "nameGap": 58,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "data": [[x, y] for x, y in zip(temperature_k_weight, weight_data)],
            "lineStyle": {"width": 2, "color": "#1f77b4"},
            "yAxisIndex": 0
        },
        {
            "name": "Deriv. Weight (%/K)",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "data": [[x, y] for x, y in zip(temperature_k_derivative, derivative_data)],
            "lineStyle": {"width": 1.5, "color": "#d62728"},
            "yAxisIndex": 1
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "PE_TGA_kelvin",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
