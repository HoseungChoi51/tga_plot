import json
import os
import re
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"

sheets = ["Raw", "Acid-washed", "Annealed"]
colors = {"Raw": "#000000", "Acid-washed": "#1f4e9c", "Annealed": "#c0392b"}

try:
    workbook = pd.ExcelFile(DATA_FILE)
except Exception as exc:
    raise SystemExit(f"Unable to read data file: {exc}")

figures = []
series = []
x_min, x_max = np.inf, -np.inf
weight_min, weight_max = np.inf, -np.inf
dtg_min, dtg_max = np.inf, -np.inf
residue_markers = []
peak_markers = []

for sheet in sheets:
    if sheet not in workbook.sheet_names:
        continue

    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    temp_col = next((c for c in df.columns if "temperature" in c.lower()), None)
    weight_col = next((c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower()), None)
    dtg_col = next((c for c in df.columns if "deriv" in c.lower()), None)
    if not (temp_col and weight_col and dtg_col):
        continue

    temp = pd.to_numeric(df[temp_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = temp.notna() & weight.notna() & dtg.notna()
    temp = temp[valid].to_numpy(dtype=float)
    weight = weight[valid].to_numpy(dtype=float)
    dtg = dtg[valid].to_numpy(dtype=float)
    if len(temp) == 0:
        continue

    # DTG is negative during mass loss; invert it so degradation peaks point upward.
    dtg_up = -dtg
    color = colors[sheet]
    weight_data = [[float(x), float(y)] for x, y in zip(temp, weight)]
    dtg_data = [[float(x), float(y)] for x, y in zip(temp, dtg_up)]

    series.extend([
        {
            "name": f"{sheet} Weight",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 0,
            "data": weight_data,
            "showSymbol": False,
            "connectNulls": True,
            "lineStyle": {"width": 2, "color": color},
            "itemStyle": {"color": color},
            "emphasis": {"focus": "series"},
        },
        {
            "name": f"{sheet} DTG",
            "type": "line",
            "xAxisIndex": 0,
            "yAxisIndex": 1,
            "data": dtg_data,
            "showSymbol": False,
            "connectNulls": True,
            "lineStyle": {"width": 1.7, "type": "dashed", "color": color},
            "itemStyle": {"color": color},
            "emphasis": {"focus": "series"},
        },
    ])

    x_min = min(x_min, float(np.min(temp)))
    x_max = max(x_max, float(np.max(temp)))
    weight_min = min(weight_min, float(np.min(weight)))
    weight_max = max(weight_max, float(np.max(weight)))
    dtg_min = min(dtg_min, float(np.min(dtg_up)))
    dtg_max = max(dtg_max, float(np.max(dtg_up)))

    residue_idx = int(np.argmin(np.abs(temp - 800)))
    residue_t = float(temp[residue_idx])
    residue_w = float(weight[residue_idx])
    residue_markers.append({
        "name": f"{sheet} residue",
        "coord": [residue_t, residue_w],
        "value": f"{sheet} Residue {residue_w:.1f}%",
        "itemStyle": {"color": color},
        "label": {"show": True, "position": "right", "fontSize": 10, "color": color},
    })

    above_150 = np.flatnonzero(temp > 150)
    if len(above_150):
        peak_idx = int(above_150[np.argmax(dtg_up[above_150])])
        peak_markers.append({
            "name": f"{sheet} DTG peak",
            "coord": [float(temp[peak_idx]), float(dtg_up[peak_idx])],
            "value": f"{sheet} {temp[peak_idx]:.0f} °C",
            "itemStyle": {"color": color},
            "label": {"show": True, "position": "top", "fontSize": 10, "color": color},
        })

if series:
    # Attach per-sample markers to their corresponding curves.
    for s in series:
        sample = s["name"].rsplit(" ", 1)[0]
        if s["name"].endswith("Weight"):
            marks = [m for m in residue_markers if m["name"].startswith(sample + " ")]
            s["markPoint"] = {"symbol": "circle", "symbolSize": 8, "data": marks}
        else:
            marks = [m for m in peak_markers if m["name"].startswith(sample + " ")]
            s["markPoint"] = {"symbol": "circle", "symbolSize": 8, "data": marks}

    dtg_span = dtg_max - dtg_min
    dtg_pad = max(0.05, dtg_span * 0.08)
    weight_pad = max(2.0, (weight_max - weight_min) * 0.08)

    option = {
        "title": {
            "text": "TGA Comparison",
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {
            "data": [s["name"] for s in series],
            "left": "center",
            "top": 32,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
        },
        "grid": {"left": 68, "right": 72, "top": 82, "bottom": 58},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 34,
            "min": float(x_min),
            "max": float(x_max),
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": max(0, float(weight_min - weight_pad)),
                "max": float(weight_max + weight_pad),
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
            },
            {
                "type": "value",
                "name": "DTG (-%/°C)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": float(dtg_min - dtg_pad),
                "max": float(dtg_max + dtg_pad),
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    figures.append({
        "name": "tga_comparison",
        "option": option,
        "width": 900,
        "height": 600,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
