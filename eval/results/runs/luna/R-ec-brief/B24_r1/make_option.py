import json
import math
import os
import re

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip().lower())

def find_column(columns, terms):
    normalized = [clean_name(c) for c in columns]
    for term in terms:
        for i, name in enumerate(normalized):
            if term in name:
                return columns[i]
    return None

def json_safe(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value

def main():
    frame = pd.read_excel(DATA_FILE, sheet_name="PE")
    frame.columns = [str(c).strip() for c in frame.columns]

    x_col = find_column(frame.columns, ["temperature", "temp"])
    weight_col = find_column(frame.columns, ["weight"])
    dtg_col = find_column(frame.columns, ["deriv", "dtg"])

    if x_col is None or weight_col is None or dtg_col is None:
        raise ValueError("PE 시트에서 온도, 무게, DTG 열을 찾을 수 없습니다.")

    x = pd.to_numeric(frame[x_col], errors="coerce").to_numpy(dtype=float) + 273.15
    weight = pd.to_numeric(frame[weight_col], errors="coerce").to_numpy(dtype=float)
    dtg = pd.to_numeric(frame[dtg_col], errors="coerce").to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        raise ValueError("PE 시트에 유효한 데이터가 없습니다.")

    # DTG의 질량 감소 피크를 위쪽으로 표시
    dtg_up = -dtg

    residue_idx = int(np.argmin(np.abs(x - (800.0 + 273.15))))
    peak_candidates = np.flatnonzero(x > (150.0 + 273.15))
    peak_idx = int(peak_candidates[np.argmax(dtg_up[peak_candidates])]) if len(peak_candidates) else int(np.argmax(dtg_up))

    weight_data = [[json_safe(a), json_safe(b)] for a, b in zip(x, weight)]
    dtg_data = [[json_safe(a), json_safe(b)] for a, b in zip(x, dtg_up)]

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#222222"},
        "title": {
            "text": "PE",
            "left": "center",
            "top": 12,
            "textStyle": {"fontSize": 18, "fontWeight": "bold"}
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": ["Weight (%)", "DTG (-%/°C)"], "left": "center", "bottom": 12},
        "grid": {"left": 78, "right": 78, "top": 68, "bottom": 76},
        "xAxis": {
            "type": "value",
            "name": "Temperature (K)",
            "nameLocation": "middle",
            "nameGap": 42,
            "min": float(np.min(x)),
            "max": float(np.max(x)),
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "axisTick": {"show": True},
            "axisLabel": {"fontSize": 11},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontSize": 11},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
            },
            {
                "type": "value",
                "name": "DTG (-%/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisTick": {"show": True},
                "axisLabel": {"fontSize": 11},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "data": weight_data,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": "Residue " + format(weight[residue_idx], ".1f") + "%",
                        "position": "right",
                        "fontSize": 11,
                        "color": "#1f4e9c"
                    },
                    "data": [{"coord": [json_safe(x[residue_idx]), json_safe(weight[residue_idx])]}]
                }
            },
            {
                "name": "DTG (-%/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": dtg_data,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "itemStyle": {"color": "#c0392b"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "itemStyle": {"color": "#c0392b"},
                    "label": {
                        "show": True,
                        "formatter": str(int(round(x[peak_idx]))) + " K",
                        "position": "top",
                        "fontSize": 11,
                        "color": "#c0392b"
                    },
                    "data": [{"coord": [json_safe(x[peak_idx]), json_safe(dtg_up[peak_idx])]}]
                }
            }
        ]
    }

    output = {
        "figures": [{
            "name": "PE",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }]
    }
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
