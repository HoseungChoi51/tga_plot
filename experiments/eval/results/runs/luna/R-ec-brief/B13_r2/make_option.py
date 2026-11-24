import json
import os
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def col_by_name(columns, pattern):
    for i, name in enumerate(columns):
        if re.search(pattern, str(name), re.I):
            return i
    return None

def find_drop_temperatures(temp, weight, count=2, min_separation=45):
    # Smooth weight, then identify the steepest local decreases in successive
    # temperature windows. Using a robust local slope suppresses point noise.
    order = np.argsort(temp)
    t = np.asarray(temp, dtype=float)[order]
    w = np.asarray(weight, dtype=float)[order]
    valid = np.isfinite(t) & np.isfinite(w)
    t, w = t[valid], w[valid]
    if len(t) < 5:
        return []

    window = max(7, min(21, len(t) // 30))
    if window % 2 == 0:
        window += 1
    smooth = pd.Series(w).rolling(window, center=True, min_periods=1).median().to_numpy()

    # Estimate the local negative slope over a fixed span and select distinct
    # maxima of the rate of weight loss.
    span = max(5, len(t) // 80)
    slopes = np.full(len(t), np.nan)
    for i in range(span, len(t) - span):
        dt = t[i + span] - t[i - span]
        if dt > 0:
            slopes[i] = -(smooth[i + span] - smooth[i - span]) / dt

    candidates = np.where(np.isfinite(slopes))[0]
    candidates = candidates[(t[candidates] >= 80) & (t[candidates] <= 850)]
    if not len(candidates):
        return []

    # Prefer peaks in rate of weight loss, requiring a meaningful local drop.
    ranked = candidates[np.argsort(slopes[candidates])[::-1]]
    chosen = []
    for idx in ranked:
        if slopes[idx] <= 0:
            break
        if all(abs(t[idx] - t[j]) >= min_separation for j in chosen):
            chosen.append(idx)
            if len(chosen) == count:
                break

    # If the two stages are close, relax separation but retain distinct points.
    if len(chosen) < count:
        for idx in ranked:
            if slopes[idx] <= 0:
                break
            if all(abs(t[idx] - t[j]) >= 20 for j in chosen):
                chosen.append(idx)
                if len(chosen) == count:
                    break
    chosen.sort(key=lambda i: t[i])
    return [(float(t[i]), float(slopes[i])) for i in chosen]

book = pd.ExcelFile(DATA_FILE)
sheet = "PVC" if "PVC" in book.sheet_names else book.sheet_names[0]
df = pd.read_excel(DATA_FILE, sheet_name=sheet)
cols = list(df.columns)
x_idx = col_by_name(cols, r"temperature|temp|온도")
y_idx = col_by_name(cols, r"weight|mass|무게|중량")
if x_idx is None:
    x_idx = 1
if y_idx is None:
    y_idx = 2

temp = pd.to_numeric(df.iloc[:, x_idx], errors="coerce").to_numpy()
weight = pd.to_numeric(df.iloc[:, y_idx], errors="coerce").to_numpy()
valid = np.isfinite(temp) & np.isfinite(weight)
temp, weight = temp[valid], weight[valid]

drops = find_drop_temperatures(temp, weight)
data = [[float(x), float(y)] for x, y in zip(temp, weight)]

mark_points = []
for x, _ in drops:
    idx = int(np.argmin(np.abs(temp - x)))
    mark_points.append({
        "coord": [float(temp[idx]), float(weight[idx])],
        "value": f"{temp[idx]:.0f} °C",
        "label": {
            "show": True,
            "position": "top",
            "formatter": f"{temp[idx]:.0f} °C",
            "color": "#c0392b",
            "fontSize": 13,
            "fontWeight": "bold"
        },
        "symbol": "circle",
        "symbolSize": 9,
        "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1}
    })

option = {
    "animation": False,
    "title": {
        "text": "PVC",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "color": "#222222"}
    },
    "tooltip": {"trigger": "axis"},
    "grid": {"left": 72, "right": 68, "top": 62, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": float(np.nanmin(temp)),
        "max": float(np.nanmax(temp)),
        "axisLabel": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12}
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 48,
        "min": 0,
        "max": 105,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12},
        "splitLine": {"show": True, "lineStyle": {"color": "#dddddd", "type": "solid"}}
    },
    "series": [{
        "name": "Weight (%)",
        "type": "line",
        "data": data,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"color": "#1f4e9c", "width": 2},
        "itemStyle": {"color": "#1f4e9c"},
        "markPoint": {
            "symbol": "circle",
            "data": mark_points,
            "label": {"show": True}
        }
    }]
}

print(json.dumps({
    "figures": [{
        "name": "PVC",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
