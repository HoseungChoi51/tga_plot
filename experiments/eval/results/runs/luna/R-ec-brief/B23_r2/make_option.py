import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

SHEET_COLORS = {
    "Raw": "#000000",
    "Acid-washed": "#1f77b4",
    "Annealed": "#c0392b",
}


def clean_name(value):
    return re.sub(r"\s+", " ", str(value).strip())


def find_column(columns, pattern, fallback):
    for i, name in enumerate(columns):
        if re.search(pattern, clean_name(name), re.IGNORECASE):
            return i
    return fallback


def finite_pairs(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


file_path = Path(DATA_FILE)
sheets = pd.read_excel(file_path, sheet_name=None, header=0)

series = []
all_x = []
weight_values = []
dtg_values = []
annotations = []

for sheet_name, frame in sheets.items():
    if frame.empty:
        continue

    columns = list(frame.columns)
    x_col = find_column(columns, r"temp", 1 if len(columns) > 1 else 0)
    weight_col = find_column(columns, r"weight(?!.*deriv)", 2 if len(columns) > 2 else 1)
    dtg_col = find_column(columns, r"deriv", 3 if len(columns) > 3 else len(columns) - 1)

    x = pd.to_numeric(frame.iloc[:, x_col], errors="coerce").to_numpy(dtype=float)
    weight = pd.to_numeric(frame.iloc[:, weight_col], errors="coerce").to_numpy(dtype=float)
    dtg = pd.to_numeric(frame.iloc[:, dtg_col], errors="coerce").to_numpy(dtype=float)

    xw, yw = finite_pairs(x, weight)
    xd, yd = finite_pairs(x, dtg)
    if len(xw) == 0 or len(xd) == 0:
        continue

    color = SHEET_COLORS.get(str(sheet_name), "#666666")
    label = str(sheet_name)

    series.append({
        "name": f"{label} Weight",
        "type": "line",
        "showSymbol": False,
        "connectNulls": False,
        "xAxisIndex": 0,
        "yAxisIndex": 0,
        "data": [[float(a), float(b)] for a, b in zip(xw, yw)],
        "lineStyle": {"width": 2, "color": color},
        "itemStyle": {"color": color},
    })
    series.append({
        "name": f"{label} DTG",
        "type": "line",
        "showSymbol": False,
        "connectNulls": False,
        "xAxisIndex": 0,
        "yAxisIndex": 1,
        "data": [[float(a), float(-b)] for a, b in zip(xd, yd)],
        "lineStyle": {"width": 1.6, "type": "dashed", "color": color, "opacity": 0.75},
        "itemStyle": {"color": color},
    })

    all_x.extend(xw.tolist())
    weight_values.extend(yw.tolist())
    dtg_values.extend((-yd).tolist())

    residue_idx = int(np.nanargmin(np.abs(xw - 800.0)))
    residue_x = float(xw[residue_idx])
    residue_y = float(yw[residue_idx])
    annotations.append({
        "name": f"{label} residue",
        "type": "scatter",
        "xAxisIndex": 0,
        "yAxisIndex": 0,
        "symbolSize": 8,
        "data": [[residue_x, residue_y]],
        "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
        "label": {
            "show": True,
            "formatter": f"{label} residue {residue_y:.1f}%",
            "position": "right",
            "color": color,
            "fontSize": 11,
        },
        "tooltip": {"show": False},
        "z": 10,
    })

    peak_mask = xd > 150.0
    if np.any(peak_mask):
        peak_x = xd[peak_mask]
        peak_y = -yd[peak_mask]
        peak_idx = int(np.nanargmax(peak_y))
        peak_temp = float(peak_x[peak_idx])
        peak_val = float(peak_y[peak_idx])
        annotations.append({
            "name": f"{label} DTG peak",
            "type": "scatter",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "symbolSize": 8,
            "data": [[peak_temp, peak_val]],
            "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": f"{label} {peak_temp:.0f} °C",
                "position": "top",
                "color": color,
                "fontSize": 11,
            },
            "tooltip": {"show": False},
            "z": 10,
        })

series.extend(annotations)

x_min = float(np.nanmin(all_x)) if all_x else 0.0
x_max = float(np.nanmax(all_x)) if all_x else 900.0
w_min = min(0.0, float(np.nanmin(weight_values))) if weight_values else 0.0
w_max = max(100.0, float(np.nanmax(weight_values))) if weight_values else 100.0
d_min = min(0.0, float(np.nanmin(dtg_values))) if dtg_values else 0.0
d_max = float(np.nanmax(dtg_values)) if dtg_values else 1.0

option = {
    "animation": False,
    "title": {
        "text": "TGA Comparison",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": [
            "Raw Weight", "Raw DTG",
            "Acid-washed Weight", "Acid-washed DTG",
            "Annealed Weight", "Annealed DTG",
        ],
        "left": "center",
        "bottom": 8,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
    },
    "grid": {"left": 72, "right": 72, "top": 60, "bottom": 82},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 32,
        "min": x_min,
        "max": x_max,
        "axisLine": {"lineStyle": {"color": "#444444"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": w_min,
            "max": w_max,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#1f4e9c"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "−DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": d_min,
            "max": d_max * 1.08 if d_max > 0 else 1.0,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#c0392b"},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "tga_comparison",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
