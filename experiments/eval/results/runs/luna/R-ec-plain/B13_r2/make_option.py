import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
SHEET = "PVC"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET)
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    for col in df.columns:
        if re.search(pattern, col, flags=re.IGNORECASE):
            return col
    raise ValueError(f"Required column not found: {pattern}")

x_col = find_column(r"Temperature")
weight_col = find_column(r"Weight\s*\(")

data = df[[x_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(x_col)
temperature = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)

# Smooth the weight trace, then locate the two most prominent negative-slope
# regions, keeping the reported temperatures at the steepest point in each.
window =  nine = 9
if len(weight) >= window:
    smooth = np.convolve(weight, np.ones(window) / window, mode="same")
else:
    smooth = weight.copy()

slope = np.gradient(smooth, temperature)
valid = np.isfinite(slope)
candidate_indices = np.where(valid)[0]
ranked = candidate_indices[np.argsort(slope[candidate_indices])]
chosen = []

# Require separated peaks so one broad drop is not marked twice.
min_separation = max(20, int(len(temperature) * 0.06))
for idx in ranked:
    if slope[idx] >= 0:
        break
    if all(abs(int(idx) - j) >= min_separation for j in chosen):
        chosen.append(int(idx))
    if len(chosen) == 2:
        break

# Fallback: split the temperature range into two parts and mark the steepest
# descent in each, if two distinct negative-slope regions were not found.
if len(chosen) < 2:
    midpoint = len(temperature) // 2
    for segment in (range(0, midpoint), range(midpoint, len(temperature))):
        candidates = [i for i in segment if slope[i] < 0 and i not in chosen]
        if candidates:
            chosen.append(min(candidates, key=lambda i: slope[i]))
        if len(chosen) == 2:
            break

chosen = sorted(chosen, key=lambda i: temperature[i])
markers = [
    {
        "name": f"급격한 무게 감소 {n}",
        "coord": [round(float(temperature[i]), 1), round(float(weight[i]), 2)],
        "value": f"{temperature[i]:.1f} °C",
        "label": {
            "show": True,
            "formatter": f"{temperature[i]:.1f} °C",
            "position": "top",
            "color": "#9b2226",
            "fontWeight": "bold",
            "backgroundColor": "rgba(255,255,255,0.88)",
            "padding": [4, 6],
            "borderRadius": 3,
        },
        "itemStyle": {"color": "#ae2012"},
    }
    for n, i in enumerate(chosen, start=1)
]

option = {
    "backgroundColor": "#ffffff",
    "title": {
        "text": "PVC 열중량 분석",
        "subtext": "무게가 급격히 감소하는 두 구간의 온도",
        "left": "center",
        "top": 12,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"},
        "subtextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12, "color": "#666"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "grid": {"left": 75, "right": 35, "top": 82, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": float(np.nanmin(temperature)),
        "max": float(np.nanmax(temperature)),
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
    },
    "yAxis": {
        "type": "value",
        "name": "무게 (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
    },
    "series": [
        {
            "name": "무게",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2.2, "color": "#2878b5"},
            "itemStyle": {"color": "#2878b5"},
            "data": [
                [round(float(x), 4), round(float(y), 4)]
                for x, y in zip(temperature, weight)
            ],
            "markPoint": {
                "symbol": "pin",
                "symbolSize": 48,
                "data": markers,
            },
        }
    ],
}

print(json.dumps(
    {
        "figures": [
            {
                "name": "pvc_weight_drop_temperatures",
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
))
