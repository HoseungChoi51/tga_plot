```python
import json
import math

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"


def safe_float(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def find_column(columns, includes, excludes=None):
    for col in columns:
        name = str(col).lower()
        if any(k in name for k in includes):
            if excludes and any(e in name for e in excludes):
                continue
            return col
    return None


def main():
    path = DATA_FILE

    try:
        xl = pd.ExcelFile(path)
        sheet_names = list(xl.sheet_names)
    except Exception:
        sheet_names = []

    color_map = {
        "Raw": "#000000",
        "Acid-washed": "#1f4e9c",
        "Annealed": "#c0392b",
    }
    default_colors = ["#000000", "#1f4e9c", "#c0392b", "#2ecc71", "#f39c12", "#8e44ad"]

    samples = []
    all_y2 = []

    for idx, sheet in enumerate(sheet_names):
        try:
            df = pd.read_excel(path, sheet_name=sheet)
        except Exception:
            continue

        if df is None or df.empty:
            continue

        cols = list(df.columns)

        x_col = find_column(cols, ["temperature", "temp"])
        y1_col = find_column(cols, ["weight"], ["deriv", "dtg"])
        y2_col = find_column(cols, ["deriv", "dtg"])

        if x_col is None and len(cols) > 1:
            x_col = cols[1]
        if y1_col is None and len(cols) > 2:
            y1_col = cols[2]
        if y2_col is None and len(cols) > 3:
            y2_col = cols[3]

        if x_col is None or y1_col is None:
            continue

        x = pd.to_numeric(df[x_col], errors="coerce")
        w = pd.to_numeric(df[y1_col], errors="coerce")

        if y2_col is None:
            dtg = pd.Series([np.nan] * len(df), index=df.index)
        else:
            dtg = pd.to_numeric(df[y2_col], errors="coerce")

        frame = pd.DataFrame({"x": x, "w": w, "dtg": dtg})
        frame = frame.dropna(subset=["x", "w"])

        if frame.empty:
            continue

        frame = frame.sort_values("x")

        xv = frame["x"].to_numpy(dtype=float)
        wv = frame["w"].to_numpy(dtype=float)
        dtgv = frame["dtg"].to_numpy(dtype=float)
        neg = -dtgv

        weight_points = []
        for a, b in zip(xv, wv):
            fa = safe_float(a)
            fb = safe_float(b)
            if fa is not None and fb is not None:
                weight_points.append([fa, fb])

        dtg_points = []
        for a, b in zip(xv, neg):
            fa = safe_float(a)
            fb = safe_float(b)
            if fa is not None and fb is not None:
                dtg_points.append([fa, fb])
                all_y2.append(fb)

        residue = None
        if len(xv) > 0:
            j = int(np.argmin(np.abs(xv - 800.0)))
            fx = safe_float(xv[j])
            fy = safe_float(wv[j])
            if fx is not None and fy is not None:
                residue = [fx, fy]

        peak = None
        if len(xv) > 0:
            mask = (xv > 150.0) & np.isfinite(neg)
            if np.any(mask):
                neg_for_max = np.where(mask, neg, -np.inf)
                j = int(np.argmax(neg_for_max))
                fx = safe_float(xv[j])
                fy = safe_float(neg[j])
                if fx is not None and fy is not None:
                    peak = [fx, fy]

        color = color_map.get(sheet, default_colors[idx % len(default_colors)])

        samples.append(
            {
                "name": sheet,
                "color": color,
                "weight_points": weight_points,
                "dtg_points": dtg_points,
                "residue": residue,
                "peak": peak,
            }
        )

    if all_y2:
        y2_min = min(0.0, min(all_y2))
        y2_max = max(all_y2)
    else:
        y2_min = 0.0
        y2_max = 1.0

    if y2_max <= y2_min:
        y2_max = y2_min + 1.0

    y2_range = y2_max - y2_min
    y2_min -= y2_range * 0.08
    y2_max += y2_range * 0.15

    y2_min = round(y2_min, 3)
    y2_max = round(y2_max, 3)

    if y2_max <= y2_min:
        y2_max = y2_min + 1.0

    series = []
    legend_names = []

    for s in samples:
        name = s["name"]
        color = s["color"]

        if name not in legend_names:
            legend_names.append(name)

        if s["weight_points"]:
            mark_data = []
            if s["residue"] is not None:
                mark_data.append(
                    {
                        "coord": s["residue"],
                        "name": f"{name} Residue {s['residue'][1]:.1f}%",
                    }
                )

            series.append(
                {
                    "id": f"{name}_weight",
                    "name": name,
                    "type": "line",
                    "xAxisIndex": 0,
                    "yAxisIndex": 0,
                    "showSymbol": False,
                    "smooth": False,
                    "connectNulls": False,
                    "z": 3,
                    "lineStyle": {
                        "color": color,
                        "width": 1.6,
                    },
                    "itemStyle": {
                        "color": color,
                    },
                    "data": s["weight_points"],
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 7,
                        "itemStyle": {
                            "color": color,
                        },
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": "{b}",
                            "fontSize": 10,
                            "color": color,
                            "distance": 4,
                        },
                        "data": mark_data,
                    },
                }
            )

        if s["dtg_points"]:
            mark_data = []
            if s["peak"] is not None:
                mark_data.append(
                    {
                        "coord": s["peak"],
                        "name": f"{name} {s['peak'][0]:.0f} °C",
                    }
                )

            series.append(
                {
                    "id": f"{name}_dtg",
                    "name": name,
                    "type": "line",
                    "xAxisIndex": 0,
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "smooth": False,
                    "connectNulls": False,
                    "z": 2,
                    "lineStyle": {
                        "color": color,
                        "width": 1.2,
                        "type": "dashed",
                    },
                    "itemStyle": {
                        "color": color,
                    },
                    "data": s["dtg_points"],
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 7,
                        "itemStyle": {
                            "color": color,
                        },
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": "{b}",
                            "fontSize": 10,
                            "color": color,
                            "distance": 4,
                        },
                        "data": mark_data,
                    },
                }
            )

    option = {
        "backgroundColor": "#ffffff",
        "title": {
            "text": "TGA",
            "left": "center",
            "top": 8,
            "textStyle": {
                "fontSize": 14,
                "color": "#000000",
            },
        },
        "legend": {
            "orient": "vertical",
            "left": 10,
            "top": "middle",
            "data": legend_names,
            "itemGap": 10,
            "textStyle": {
                "fontSize": 11,
                "color": "#333333",
            },
        },
        "grid": {
            "left": 115,
            "right": 70,
            "top": 55,
            "bottom": 50,
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
            },
        },
        "xAxis": [
            {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 28,
                "min": 0,
                "max": 900,
                "axisLine": {
                    "show": True,
                    "lineStyle": {
                        "color": "#333333",
                    },
                },
                "axisTick": {
                    "show": True,
                },
                "axisLabel": {
                    "fontSize": 11,
                    "color": "#333333",
                },
                "splitLine": {
                    "