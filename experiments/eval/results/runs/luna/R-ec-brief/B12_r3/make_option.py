import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)

# Use the columns identified in the data preview.
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()
valid = np.isfinite(temperature) & np.isfinite(weight)
temperature, weight = temperature[valid], weight[valid]

# Label the measured weight nearest to 900 °C.
idx = int(np.argmin(np.abs(temperature - 900)))
residue_temp = float(temperature[idx])
residue_weight = float(weight[idx])

option = {
    "title": {
        "text": "caox",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 76, "right": 28, "top": 64, "bottom": 68},
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
        "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 10,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "plot1",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False))
