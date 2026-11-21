import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip()).lower()

def find_column(columns, patterns):
    for col in columns:
        name = clean_name(col)
        if any(re.search(pattern, name) for pattern in patterns):
            return col
    return None

def json_num(value):
    return float(value) if np.isfinite(value) else None

book = pd.ExcelFile(DATA_FILE)
sheet = next((s for s in book.sheet_names if clean_name(s) == "annealed"), None)

figures = []
if sheet is not None:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = find_column(df.columns, [r"temperature", r"temp.*°?c"])
    weight_col = find_column(df.columns, [r"weight\s*\(?%?\)?", r"mass.*%"])
    dtg_col = find_column(df.columns, [r"deriv", r"\bdtg\b"])

    if x_col is None or weight_col is None or dtg_col is None:
        raise ValueError("Annealed 시트에서 온도, 중량, DTG 열을 찾을 수 없습니다.")

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(x_col).drop_duplicates(subset=x_col, keep="first")
    temperature = data[x_col].to_numpy(dtype=float)
    weight = data[weight_col].to_numpy(dtype=float)
    dtg = data[dtg_col].to_numpy(dtype=float)

    # DTG는 질량 감소에서 음수이므로, 가장 깊은 감소 피크(150 °C 초과)를 사용한다.
    peak_candidates = np.flatnonzero((temperature > 150) & (dtg < 0))
    onset_temp = None
    onset_weight = None
    peak_index = None

    if len(peak_candidates):
        peak_index = int(peak_candidates[np.argmin(dtg[peak_candidates])])

        # 피크 직전의 가장 가까운 국소 최소를 분해 단계의 시작점으로 삼고,
        # 그 지점 이전의 안정 구간을 기준선으로 선형 외삽한다.
        minima = [
            i for i in range(1, peak_index)
            if dtg[i] <= dtg[i - 1] and dtg[i] < dtg[i + 1]
        ]
        start_index = minima[-1] if minima else max(0, peak_index - 1)

        baseline_end = start_index
        baseline_start = max(0, baseline_end - 24)
        baseline_idx = np.arange(baseline_start, baseline_end + 1)
        baseline_idx = baseline_idx[temperature[baseline_idx] < temperature[start_index]]
        if len(baseline_idx) < 3:
            baseline_idx = np.arange(max(0, start_index - 5), start_index + 1)

        # 안정 구간 DTG의 중앙값을 기준선으로 보고, DTG 하강 구간에
        # 기준선과 접선이 만나는 외삽 개시점을 계산한다.
        baseline = float(np.median(dtg[baseline_idx])) if len(baseline_idx) else float(dtg[start_index])
        left = max(0, peak_index - 30)
        right = peak_index + 1
        slope_candidates = np.arange(left, right)
        below = slope_candidates[dtg[slope_candidates] < baseline]
        if len(below):
            cross = int(below[0])
            if cross > 0 and dtg[cross] != dtg[cross - 1]:
                frac = (baseline - dtg[cross - 1]) / (dtg[cross] - dtg[cross - 1])
                onset_temp = float(temperature[cross - 1] + frac * (temperature[cross] - temperature[cross - 1]))
            else:
                onset_temp = float(temperature[cross])

            # onset에서 가장 가파른 상승(질량 감소) 접선으로 외삽
            end = min(peak_index, cross + 20)
            segment = np.arange(cross, end + 1)
            if len(segment) >= 2:
                slopes = np.diff(dtg[segment]) / np.diff(temperature[segment])
                j = int(np.argmax(slopes))
                i0, i1 = int(segment[j]), int(segment[j + 1])
                slope = (dtg[i1] - dtg[i0]) / (temperature[i1] - temperature[i0])
                if slope > 0:
                    onset_temp = float(temperature[i0] + (baseline - dtg[i0]) / slope)
            onset_temp = float(np.clip(onset_temp, temperature[0], temperature[peak_index]))
            onset_weight = float(np.interp(onset_temp, temperature, weight))

    residue_index = int(np.argmin(np.abs(temperature - 800)))
    peak_temp = float(temperature[peak_index]) if peak_index is not None else None

    series = [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 0,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[json_num(x), json_num(y)] for x, y in zip(temperature, weight)],
        },
        {
            "name": "-DTG",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 1,
            "lineStyle": {"color": "#c0392b", "width": 1.7},
            "data": [[json_num(x), json_num(-y)] for x, y in zip(temperature, dtg)],
        },
        {
            "name": "Residue",
            "type": "scatter",
            "yAxisIndex": 0,
            "symbolSize": 9,
            "itemStyle": {"color": "#1f4e9c"},
            "data": [{
                "value": [json_num(temperature[residue_index]), json_num(weight[residue_index])],
                "label": {
                    "show": True,
                    "formatter": f"Residue {weight[residue_index]:.1f}%",
                    "position": "right",
                    "color": "#1f4e9c",
                    "fontSize": 12,
                },
            }],
        },
    ]

    if peak_index is not None:
        series.append({
            "name": "DTG peak",
            "type": "scatter",
            "yAxisIndex": 1,
            "symbolSize": 9,
            "itemStyle": {"color": "#c0392b"},
            "data": [{
                "value": [peak_temp, json_num(-dtg[peak_index])],
                "label": {
                    "show": True,
                    "formatter": f"{peak_temp:.0f} °C",
                    "position": "top",
                    "color": "#c0392b",
                    "fontSize": 12,
                },
            }],
        })

    if onset_temp is not None:
        series.append({
            "name": "Extrapolated onset",
            "type": "scatter",
            "yAxisIndex": 1,
            "symbol": "diamond",
            "symbolSize": 11,
            "itemStyle": {"color": "#2e8b57"},
            "data": [{
                "value": [json_num(onset_temp), json_num(-float(np.interp(onset_temp, temperature, dtg)))],
                "label": {
                    "show": True,
                    "formatter": f"Onset {onset_temp:.0f} °C",
                    "position": "bottom",
                    "color": "#2e8b57",
                    "fontSize": 12,
                },
            }],
        })

    option = {
        "animation": False,
        "title": {
            "text": sheet,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"left": "center", "bottom": 4},
        "grid": {"left": 66, "right": 66, "top": 58, "bottom": 70},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "axisLine": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
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
                "axisLabel": {"color": "#1f4e9c"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisLabel": {"color": "#c0392b"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    figures.append({
        "name": "annealed_onset",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
