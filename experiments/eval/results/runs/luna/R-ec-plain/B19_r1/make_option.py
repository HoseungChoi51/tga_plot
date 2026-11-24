import json
import os

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="PVC")
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)

order = np.argsort(temperature)
temperature = temperature[order]
weight = weight[order]

def weight_at(target):
    return float(np.interp(target, temperature, weight))

t_start, t_end = 200.0, 400.0
w_start = weight_at(t_start)
w_end = weight_at(t_end)
mass_loss = w_start - w_end

# Restrict the displayed curve to the requested temperature interval,
# adding interpolated values at both boundaries.
inside = (temperature > t_start) & (temperature < t_end)
plot_t = np.concatenate(([t_start], temperature[inside], [t_end]))
plot_w = np.concatenate(([w_start], weight[inside], [w_end]))

figures = [{
    "name": "pvc_mass_loss_200_400C",
    "width": 760,
    "height": 520,
    "dpi": 300,
    "formats": ["png"],
    "option": {
        "backgroundColor": "#ffffff",
        "animation": False,
        "title": {
            "text": "PVC 질량 감소 (200–400 °C)",
            "subtext": f"질량 감소량: {mass_loss:.2f}%  |  200 °C: {w_start:.2f}% → 400 °C: {w_end:.2f}%",
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"},
            "subtextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 13, "color": "#444"}
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "line"},
            "valueFormatter": "{value}"
        },
        "grid": {"left": 78, "right": 35, "top": 105, "bottom": 72},
        "xAxis": {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": t_start,
            "max": t_end,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        "yAxis": {
            "type": "value",
            "name": "질량 (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 100,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"lineStyle": {"color": "#e6e6e6"}}
        },
        "series": [
            {
                "name": "질량",
                "type": "line",
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {"width": 2.5, "color": "#2878B5"},
                "data": [[float(x), float(y)] for x, y in zip(plot_t, plot_w)],
                "markLine": {
                    "symbol": ["none", "none"],
                    "lineStyle": {"type": "dashed", "color": "#d9534f", "width": 1.5},
                    "label": {
                        "show": True,
                        "fontFamily": "Noto Sans CJK KR",
                        "formatter": "200 °C: {c}"
                    },
                    "data": [
                        {"xAxis": t_start, "name": "200 °C"},
                        {"xAxis": t_end, "name": "400 °C"}
                    ]
                }
            },
            {
                "name": "구간 질량 감소",
                "type": "line",
                "showSymbol": False,
                "lineStyle": {"opacity": 0},
                "data": [[t_start, w_start], [t_end, w_end]],
                "markArea": {
                    "silent": True,
                    "itemStyle": {"color": "rgba(242, 142, 43, 0.18)"},
                    "data": [[{"xAxis": t_start, "yAxis": w_start}, {"xAxis": t_end, "yAxis": w_end}]]
                }
            }
        ],
        "graphic": [{
            "type": "text",
            "left": "center",
            "bottom": 18,
            "style": {
                "text": f"200–400 °C 질량 감소량 = {mass_loss:.2f}%",
                "font": "bold 15px Noto Sans CJK KR",
                "fill": "#333"
            }
        }]
    }
}]

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
