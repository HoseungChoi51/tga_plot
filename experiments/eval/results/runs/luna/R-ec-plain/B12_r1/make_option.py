import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")

valid = temperature.notna() & weight.notna() & (temperature >= 100) & (temperature <= 900)
points = [[float(x), float(y)] for x, y in zip(temperature[valid], weight[valid])]

at_900 = pd.DataFrame({"temperature": temperature, "weight": weight}).dropna()
residue = float(
    at_900.loc[at_900["temperature"].sub(900).abs().idxmin(), "weight"]
)

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "grid": {"left": 72, "right": 38, "top": 42, "bottom": 62},
    "tooltip": {"trigger": "axis"},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 100,
        "max": 900,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "scale": True,
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "data": points,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": "#2369a1"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "data": [
                    {
                        "coord": [900, residue],
                        "value": residue,
                        "itemStyle": {"color": "#c43c39"},
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": f"Residue at 900 °C: {residue:.2f}%",
                            "fontFamily": "Noto Sans CJK KR",
                            "fontSize": 12,
                        },
                    }
                ],
            },
        }
    ],
}

print(json.dumps({
    "figures": [{
        "name": "weight_curve",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False))
