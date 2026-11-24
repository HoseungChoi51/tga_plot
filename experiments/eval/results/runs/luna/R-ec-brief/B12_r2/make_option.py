import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next((c for c in df.columns if "temperature" in c.lower()), df.columns[1])
weight_col = next((c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower()), df.columns[2])

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)

order = np.argsort(temperature)
temperature = temperature[order]
weight = weight[order]

target_temp = 900.0
nearest_index = int(np.argmin(np.abs(temperature - target_temp)))
residue_temp = float(temperature[nearest_index])
residue_weight = float(weight[nearest_index])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {
        "fontFamily": "Noto Sans CJK KR, sans-serif",
        "color": "#333333"
    },
    "title": {
        "text": os.path.splitext(os.path.basename(DATA_FILE))[0],
        "left": "center",
        "textStyle": {"fontSize": 16, "fontWeight": "normal"}
    },
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 72, "right": 34, "top": 58, "bottom": 64},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 100,
        "max": 900,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [
                [float(x), float(y)]
                for x, y in zip(temperature, weight)
                if 100 <= x <= 900
            ],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontSize": 12
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "caox",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
