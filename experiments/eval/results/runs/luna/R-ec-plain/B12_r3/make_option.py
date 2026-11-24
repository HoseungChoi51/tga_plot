import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)

data = []
for temp, weight in zip(df[temperature_col], df[weight_col]):
    if pd.notna(temp) and pd.notna(weight) and 100 <= float(temp) <= 900:
        data.append([float(temp), float(weight)])

if not data:
    raise ValueError("No valid weight data found between 100 and 900 °C.")

residue = min(data, key=lambda point: abs(point[0] - 900))
residue_temp, residue_weight = residue

option = {
    "animation": False,
    "grid": {"left": 75, "right": 35, "top": 55, "bottom": 65},
    "tooltip": {
        "trigger": "axis",
        "valueFormatter": None
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 100,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "scale": True
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#2369a8"},
            "itemStyle": {"color": "#2369a8"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 10,
                "itemStyle": {"color": "#d33f49"},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": f"Residue at 900 °C\\n{residue_weight:.2f}%",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12,
                    "color": "#333"
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        }
    ]
}

result = {
    "figures": [
        {
            "name": "weight_curve",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }
    ]
}

print(json.dumps(result, ensure_ascii=False, allow_nan=False))
