import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def clean(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def main():
    book = pd.ExcelFile(DATA_FILE)
    sheet_name = next((s for s in book.sheet_names if s.strip().lower() == "pvc"), None)
    if sheet_name is None:
        raise ValueError("PVC 시트를 찾을 수 없습니다.")

    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    cols = list(df.columns)

    def find_col(pattern):
        return next((c for c in cols if re.search(pattern, str(c), re.I)), None)

    x_col = find_col(r"temperature|온도") or cols[1]
    weight_col = find_col(r"weight|무게|중량") or cols[2]
    dtg_col = find_col(r"deriv|dtg|미분") or (cols[3] if len(cols) > 3 else None)

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(weight)
    x, weight = x[valid], weight[valid]
    order = np.argsort(x)
    x, weight = x[order], weight[order]

    # 두 번의 급격한 무게 감소 구간을 -d(weight)/dT 기준으로 찾는다.
    if dtg_col is not None:
        dtg_all = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)[valid][order]
        rate = -dtg_all
        rate = np.where(np.isfinite(rate), rate, 0.0)
    else:
        rate = -np.gradient(weight, x)

    peak_indices, _ = find_peaks(rate, prominence=max(float(np.nanmax(rate)) * 0.035, 1e-12))
    peak_indices = [int(i) for i in peak_indices if x[i] > 150]
    peak_indices.sort(key=lambda i: rate[i], reverse=True)

    chosen = []
    for i in peak_indices:
        if all(abs(x[i] - x[j]) >= 40 for j in chosen):
            chosen.append(i)
        if len(chosen) == 2:
            break

    if len(chosen) < 2:
        candidates = np.argsort(np.nan_to_num(rate, nan=-np.inf))[::-1]
        for i in candidates:
            i = int(i)
            if x[i] > 150 and all(abs(x[i] - x[j]) >= 40 for j in chosen):
                chosen.append(i)
            if len(chosen) == 2:
                break

    chosen.sort(key=lambda i: x[i])
    labels = [f"{x[i]:.0f} °C" for i in chosen]
    marks = [
        {
            "coord": [clean(x[i]), clean(weight[i])],
            "value": labels[k],
            "label": {
                "show": True,
                "formatter": labels[k],
                "position": "top",
                "color": "#333333",
                "fontSize": 12,
                "fontFamily": "Noto Sans CJK KR",
                "backgroundColor": "rgba(255,255,255,0.85)",
                "padding": [3, 5]
            }
        }
        for k, i in enumerate(chosen)
    ]

    option = {
        "animation": False,
        "title": {
            "text": "PVC",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight (%)"], "left": "center", "bottom": 8},
        "grid": {"left": 65, "right": 65, "top": 55, "bottom": 55},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 32,
            "min": 30,
            "max": 900,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 45,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
        },
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "showSymbol": False,
                "connectNulls": False,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "data": [[clean(a), clean(b)] for a, b in zip(x, weight)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 10,
                    "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 1},
                    "data": marks
                }
            }
        ]
    }

    result = {
        "figures": [{
            "name": "pvc_weight_drop_temperatures",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }]
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
