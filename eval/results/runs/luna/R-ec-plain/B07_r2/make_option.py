import json
import math
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name=1)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "temperature" in c.lower())
weight_col = next(c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower())

data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(temperature_col)

temperatures = data[temperature_col].to_numpy()
weights = data[weight_col].to_numpy()

markers = []
for target in (300, 600):
    weight_at_target = float(
        weights[abs(temperatures - target).argmin()]
    )
    markers.append({
        "name": f"{target} °C: {weight_at_target:.2f}%",
        "coord": [target, weight_at_target],
        "value": f"{weight_at_target:.2f}%",
        "symbol": "circle",
        "symbolSize": 12,
        "itemStyle": {"color": "#d62728", "borderColor": "#ffffff", "borderWidth": 2},
        "label": {
            "show": True,
            "formatter": f"{target} °C\n{weight_at_target:.2f}%",
            "position": "top",
            "distance": 8,
            "color": "#a61c1c",
            "fontSize": 12,
            "fontWeight": "bold",
            "backgroundColor": "rgba(255,255,255,0.85)",
            "padding": [4, 6],
            "borderRadius": 3,
        },
    })

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#333333"},
    "title": {
        "text": "PVC 열중량 분석",
        "subtext": "300 °C 및 600 °C에서의 잔류 무게",
        "left": "center",
        "top": 12,
        "textStyle": {"fontSize": 18, "fontWeight": "bold"},
        "subtextStyle": {"fontSize": 12, "color": "#666666"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "valueFormatter": "{value}%",
    },
    "grid": {"left": 72, "right": 30, "top": 88, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#777777"}},
        "axisLabel": {"color": "#555555"},
        "splitLine": {"show": False},
    },
    "yAxis": {
        "type": "value",
        "name": "무게 (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"show": True, "lineStyle": {"color": "#777777"}},
        "axisLabel": {"color": "#555555"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
    },
    "series": [{
        "name": "무게",
        "type": "line",
        "data": [
            [float(x), float(y)]
            for x, y in zip(temperatures, weights)
            if math.isfinite(float(x)) and math.isfinite(float(y))
        ],
        "showSymbol": False,
        "lineStyle": {"width": 2.5, "color": "#2878b5"},
        "itemStyle": {"color": "#2878b5"},
        "markPoint": {"data": markers},
    }],
}

print(json.dumps({
    "figures": [{
        "name": "pvc_weight_at_300_600C",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
