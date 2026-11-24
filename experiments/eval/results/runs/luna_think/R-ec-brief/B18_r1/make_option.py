import json
import os
import re

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
SHEET_NAME = "Annealed"

def clean_number(value):
    try:
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def main():
    frame = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    frame.columns = [str(c).strip() for c in frame.columns]

    def find_column(pattern):
        for column in frame.columns:
            if re.search(pattern, column, flags=re.IGNORECASE):
                return column
        return None

    x_col = find_column(r"temperature|temp")
    weight_col = find_column(r"weight")
    dtg_col = find_column(r"deriv|dtg")

    if x_col is None or weight_col is None or dtg_col is None:
        raise ValueError("Could not identify temperature, weight, and DTG columns.")

    data = frame[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(x_col)
    x = data[x_col].to_numpy(dtype=float)
    weight = data[weight_col].to_numpy(dtype=float)
    dtg = data[dtg_col].to_numpy(dtype=float)

    # Locate the strongest mass-loss DTG peak above 150 °C.
    eligible = np.flatnonzero(x > 150)
    peak_idx = eligible[np.argmax(-dtg[eligible])]
    peak_temp = float(x[peak_idx])

    # Find the steepest descending part of the weight curve near that DTG peak.
    # A local linear fit gives a robust tangent rather than relying on a single
    # potentially noisy point.
    window = (x >= peak_temp - 12) & (x <= peak_temp + 12)
    local_x = x[window]
    local_weight = weight[window]
    if len(local_x) < 3:
        local_x = x[max(0, peak_idx - 2):min(len(x), peak_idx + 3)]
        local_weight = weight[max(0, peak_idx - 2):min(len(x), peak_idx + 3)]

    local_slope = np.gradient(local_weight, local_x)
    tangent_idx_local = int(np.argmin(local_slope))
    tangent_center = float(local_x[tangent_idx_local])

    # Fit the tangent over a small neighborhood around the steepest point.
    fit_window = np.abs(local_x - tangent_center) <= 5
    if np.count_nonzero(fit_window) < 2:
        fit_window = np.ones(len(local_x), dtype=bool)
    slope, intercept = np.polyfit(local_x[fit_window], local_weight[fit_window], 1)

    # Estimate the pre-event baseline immediately before the tangent region.
    before = (x >= tangent_center - 70) & (x <= tangent_center - 15)
    if np.count_nonzero(before) < 3:
        before = (x < tangent_center) & (x >= tangent_center - 100)
    baseline_weight = float(np.median(weight[before])) if np.any(before) else float(weight[0])

    onset_temp = (baseline_weight - intercept) / slope if slope != 0 else tangent_center
    if not np.isfinite(onset_temp) or onset_temp > tangent_center or onset_temp < x[0]:
        onset_temp = tangent_center

    onset_weight = baseline_weight
    residue_idx = int(np.argmin(np.abs(x - 800)))
    residue_temp = float(x[residue_idx])
    residue = float(weight[residue_idx])

    onset_line = [
        [clean_number(onset_temp), clean_number(onset_weight)],
        [clean_number(tangent_center), clean_number(slope * tangent_center + intercept)],
    ]

    option = {
        "animation": False,
        "title": {
            "text": SHEET_NAME,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Weight", "-DTG"], "left": "center", "top": 36},
        "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": clean_number(float(np.min(x))),
            "max": clean_number(float(np.max(x))),
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 48,
                "inverse": False,
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
        ],
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "data": [[clean_number(a), clean_number(b)] for a, b in zip(x, weight)],
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "itemStyle": {"color": "#1f4e9c"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 9,
                    "data": [
                        {
                            "name": "Residue",
                            "coord": [clean_number(residue_temp), clean_number(residue)],
                            "itemStyle": {"color": "#1f4e9c"},
                            "label": {
                                "show": True,
                                "formatter": f"Residue {residue:.1f}%",
                                "position": "right",
                                "fontFamily": "Noto Sans CJK KR",
                            },
                        },
                        {
                            "name": "Extrapolated onset",
                            "coord": [clean_number(onset_temp), clean_number(onset_weight)],
                            "itemStyle": {"color": "#e67e22"},
                            "label": {
                                "show": True,
                                "formatter": f"Onset {onset_temp:.0f} °C",
                                "position": "top",
                                "fontFamily": "Noto Sans CJK KR",
                            },
                        },
                    ],
                },
                "markLine": {
                    "symbol": ["none", "none"],
                    "silent": True,
                    "data": [
                        {
                            "xAxis": clean_number(onset_temp),
                            "lineStyle": {"color": "#e67e22", "type": "dashed", "width": 1.5},
                            "label": {
                                "show": True,
                                "formatter": f"Onset {onset_temp:.0f} °C",
                                "position": "insideEndTop",
                                "fontFamily": "Noto Sans CJK KR",
                            },
                        }
                    ],
                },
            },
            {
                "name": "-DTG",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "data": [[clean_number(a), clean_number(-b)] for a, b in zip(x, dtg)],
                "lineStyle": {"color": "#c0392b", "width": 1.5},
                "itemStyle": {"color": "#c0392b"},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 8,
                    "data": [
                        {
                            "name": "DTG peak",
                            "coord": [clean_number(peak_temp), clean_number(-dtg[peak_idx])],
                            "itemStyle": {"color": "#c0392b"},
                            "label": {
                                "show": True,
                                "formatter": f"{peak_temp:.0f} °C",
                                "position": "top",
                                "fontFamily": "Noto Sans CJK KR",
                            },
                        }
                    ],
                },
            },
            {
                "name": "Onset tangent",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "silent": True,
                "data": onset_line,
                "lineStyle": {"color": "#e67e22", "type": "dashed", "width": 1.5},
                "itemStyle": {"color": "#e67e22"},
            },
        ],
    }

    result = {
        "figures": [
            {
                "name": "annealed_onset",
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
