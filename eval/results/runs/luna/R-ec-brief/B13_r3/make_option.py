import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"


def clean_number(value):
    value = float(value)
    return value if np.isfinite(value) else None


def main():
    df = pd.read_excel(DATA_FILE, sheet_name="PVC")
    df.columns = [str(c).strip() for c in df.columns]

    def find_col(pattern):
        for col in df.columns:
            if re.search(pattern, col, re.I):
                return col
        return None

    x_col = find_col(r"temperature|temp|온도")
    weight_col = find_col(r"weight|무게|중량")
    dtg_col = find_col(r"deriv|dtg|미분")

    if x_col is None or weight_col is None:
        raise ValueError("PVC 시트에서 온도 및 무게 열을 찾지 못했습니다.")

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(weight)
    x, weight = x[valid], weight[valid]

    if dtg_col is not None:
        dtg_all = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)[valid]
        loss_signal = -dtg_all
    else:
        order = np.argsort(x)
        x, weight = x[order], weight[order]
        loss_signal = -np.gradient(weight, x)

    order = np.argsort(x)
    x, weight, loss_signal = x[order], weight[order], loss_signal[order]

    # 급격한 무게 감소를 나타내는 DTG 피크 두 개를 찾고,
    # 작은 어깨 피크 대신 뚜렷한 두 단계가 선택되도록 prominence를 적용합니다.
    finite_signal = np.nan_to_num(loss_signal, nan=0.0, posinf=0.0, neginf=0.0)
    peaks, props = find_peaks(
        finite_signal,
        prominence=max(float(np.nanmax(finite_signal)) * 0.035, 1e-9),
        distance=max(1, len(finite_signal) // 30),
    )

    # 주요 무게 감소 구간(통상 150 °C 이상)에 한정합니다.
    eligible = peaks[x[peaks] >= 150]
    if len(eligible) < 2:
        eligible = peaks

    if len(eligible) >= 2:
        chosen = sorted(
            eligible,
            key=lambda idx: finite_signal[idx],
            reverse=True,
        )[:2]
        chosen = sorted(chosen, key=lambda idx: x[idx])
    else:
        # DTG가 없거나 뚜렷한 두 피크가 검출되지 않으면 무게 감소 기울기의
        # 강한 두 구간을 일정 간격을 두고 선택합니다.
        candidates = np.argsort(finite_signal)[::-1]
        chosen = []
        min_gap = max(1, len(x) // 12)
        for idx in candidates:
            if x[idx] < 150:
                continue
            if all(abs(int(idx) - int(prev)) >= min_gap for prev in chosen):
                chosen.append(int(idx))
            if len(chosen) == 2:
                break
        if len(chosen) < 2:
            chosen = list(np.linspace(0, len(x) - 1, min(2, len(x)), dtype=int))
        chosen = sorted(chosen, key=lambda idx: x[idx])

    markers = [
        {
            "coord": [clean_number(x[idx]), clean_number(weight[idx])],
            "value": clean_number(x[idx]),
            "name": f"{x[idx]:.0f} °C",
            "label": {
                "show": True,
                "formatter": f"{x[idx]:.0f} °C",
                "position": "top",
                "color": "#333333",
                "fontSize": 12,
                "backgroundColor": "rgba(255,255,255,0.85)",
                "padding": [3, 5],
            },
            "itemStyle": {"color": "#c0392b"},
        }
        for idx in chosen
    ]

    x_data = [[clean_number(a), clean_number(b)] for a, b in zip(x, weight)]
    if dtg_col is not None:
        dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)[valid][order]
        dtg_data = [[clean_number(a), clean_number(-b)] for a, b in zip(x, dtg)]
    else:
        dtg_data = [[clean_number(a), clean_number(b)] for a, b in zip(x, loss_signal)]

    option = {
        "animation": False,
        "title": {
            "text": "PVC",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight (%)", "DTG (-, %/°C)"], "left": "center", "top": 30},
        "grid": {"left": 72, "right": 72, "top": 78, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": 900,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"show": True},
            "splitLine": {"show": False},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisLabel": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisLabel": {"show": True},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight (%)",
                "type": "line",
                "showSymbol": False,
                "data": x_data,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "markPoint": {"symbol": "circle", "symbolSize": 9, "data": markers},
            },
            {
                "name": "DTG (-, %/°C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": dtg_data,
                "lineStyle": {"color": "#c0392b", "width": 1.5},
                "itemStyle": {"color": "#c0392b"},
            },
        ],
    }

    result = {
        "figures": [
            {
                "name": "PVC",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        ]
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
