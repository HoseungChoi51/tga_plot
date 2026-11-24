import json
import os
import re
import sys

import numpy as np
import pandas as pd

DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]

COLORS = ["#1f4e9c", "#e67e22"]
DTG_COLORS = ["#c0392b", "#27ae60"]
NAMES = ["Lot A", "Lot B"]


def read_data(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    elif ext in (".txt", ".tsv"):
        try:
            df = pd.read_csv(path, sep=None, engine="python")
        except Exception:
            df = pd.read_csv(path, delim_whitespace=True)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")

    # Handle text files that are whitespace- or tab-delimited despite a CSV-like header.
    if len(df.columns) < 3:
        for sep in (r"\s+", "\t", ",", ";"):
            try:
                candidate = pd.read_csv(path, sep=sep, engine="python")
                if len(candidate.columns) >= 3:
                    df = candidate
                    break
            except Exception:
                pass
    return df


def numeric_column(df, pattern):
    for col in df.columns:
        if re.search(pattern, str(col), flags=re.I):
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().any():
                return values.to_numpy(dtype=float)
    return None


def clean_pairs(x, y):
    n = min(len(x), len(y))
    x, y = np.asarray(x[:n], dtype=float), np.asarray(y[:n], dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


series = []
all_temperatures = []

for idx, path in enumerate(DATA_FILES):
    df = read_data(path)
    temperature = numeric_column(df, r"temperature|temp")
    weight = numeric_column(df, r"weight\s*\(%\)|weight")
    dtg = numeric_column(df, r"deriv|dtg")

    # Fall back to the expected TGA column positions when headers are unexpected.
    if temperature is None and len(df.columns) > 1:
        temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy(dtype=float)
    if weight is None and len(df.columns) > 2:
        weight = pd.to_numeric(df.iloc[:, 2], errors="coerce").to_numpy(dtype=float)
    if dtg is None and len(df.columns) > 3:
        dtg = pd.to_numeric(df.iloc[:, 3], errors="coerce").to_numpy(dtype=float)

    if temperature is None or weight is None or dtg is None:
        raise ValueError(f"Could not identify temperature, weight, and DTG columns in {path}")

    xw, yw = clean_pairs(temperature, weight)
    xd, yd = clean_pairs(temperature, dtg)
    if len(xw) == 0 or len(xd) == 0:
        continue

    # Residue marker: measured weight nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(xw - 800.0)))
    residue_x, residue_y = float(xw[residue_idx]), float(yw[residue_idx])

    # DTG is negative during mass loss; negate it so peaks point upward.
    dtg_positive = -yd
    peak_mask = xd > 150
    if peak_mask.any():
        peak_indices = np.flatnonzero(peak_mask)
        peak_idx = int(peak_indices[np.argmax(dtg_positive[peak_mask])])
        peak_x, peak_y = float(xd[peak_idx]), float(dtg_positive[peak_idx])
    else:
        peak_x = peak_y = None

    name = NAMES[idx] if idx < len(NAMES) else os.path.splitext(os.path.basename(path))[0]
    series.append(
        {
            "name": name,
            "xw": xw,
            "yw": yw,
            "xd": xd,
            "dtg": dtg_positive,
            "residue": (residue_x, residue_y),
            "peak": (peak_x, peak_y),
            "color": COLORS[idx % len(COLORS)],
            "dtg_color": DTG_COLORS[idx % len(DTG_COLORS)],
        }
    )
    all_temperatures.extend(xw.tolist())

series_data = []
legend = []
for item in series:
    name = item["name"]
    legend.extend([f"{name} Weight", f"{name} DTG"])
    series_data.append(
        {
            "name": f"{name} Weight",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[float(x), float(y)] for x, y in zip(item["xw"], item["yw"])],
            "showSymbol": False,
            "connectNulls": True,
            "lineStyle": {"width": 2, "color": item["color"]},
            "itemStyle": {"color": item["color"]},
        }
    )
    series_data.append(
        {
            "name": f"{name} DTG",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": [[float(x), float(y)] for x, y in zip(item["xd"], item["dtg"])],
            "showSymbol": False,
            "connectNulls": True,
            "lineStyle": {"width": 1.8, "color": item["dtg_color"]},
            "itemStyle": {"color": item["dtg_color"]},
        }
    )

    rx, ry = item["residue"]
    series_data.append(
        {
            "name": f"{name} Residue",
            "type": "scatter",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": [[rx, ry]],
            "symbolSize": 9,
            "itemStyle": {"color": item["color"], "borderColor": "#ffffff", "borderWidth": 1},
            "label": {
                "show": True,
                "formatter": f"{name} Residue {ry:.1f}%",
                "position": "top",
                "fontSize": 11,
                "color": item["color"],
            },
            "tooltip": {"show": False},
        }
    )
    if item["peak"][0] is not None:
        px, py = item["peak"]
        series_data.append(
            {
                "name": f"{name} Peak",
                "type": "scatter",
                "xAxisIndex": 0,
                "yAxisIndex": 1,
                "data": [[px, py]],
                "symbolSize": 9,
                "itemStyle": {"color": item["dtg_color"], "borderColor": "#ffffff", "borderWidth": 1},
                "label": {
                    "show": True,
                    "formatter": f"{name} {px:.0f} °C",
                    "position": "top",
                    "fontSize": 11,
                    "color": item["dtg_color"],
                },
                "tooltip": {"show": False},
            }
        )

xmin = min(all_temperatures) if all_temperatures else 0
xmax = max(all_temperatures) if all_temperatures else 900

option = {
    "animation": False,
    "title": {
        "text": "TGA Comparison",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {
        "data": legend,
        "left": "center",
        "bottom": 8,
        "type": "scroll",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
    },
    "grid": {"left": 72, "right": 72, "top": 58, "bottom": 82},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 32,
        "min": float(xmin),
        "max": float(xmax),
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "DTG (-%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "inverse": False,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": series_data,
}

print(
    json.dumps(
        {
            "figures": [
                {
                    "name": "tga_lot_comparison",
                    "option": option,
                    "width": 900,
                    "height": 600,
                    "dpi": 300,
                    "formats": ["png"],
                }
            ]
        },
        ensure_ascii=False,
        allow_nan=False,
    )
)
