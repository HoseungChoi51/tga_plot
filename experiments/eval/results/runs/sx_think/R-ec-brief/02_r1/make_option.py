```python
import sys
import json
import math
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
TARGET_SHEET = "1006R1-V normal"


def ceil_to_step(value, step):
    return math.ceil(round(value / step, 10)) * step


def floor_to_step(value, step):
    return math.floor(round(value / step, 10)) * step


def main():
    try:
        xls = pd.ExcelFile(DATA_FILE)
        sheet_names = xls.sheet_names
        actual_sheet = TARGET_SHEET if TARGET_SHEET in sheet_names else (sheet_names[0] if sheet_names else "plot1")
        df = pd.read_excel(xls, sheet_name=actual_sheet, header=0)
    except Exception:
        actual_sheet = TARGET_SHEET
        df = pd.read_excel(DATA_FILE, sheet_name=actual_sheet, header=0)

    if df.shape[1] < 4:
        x_col = 1 if df.shape[1] > 1 else 0
        y1_col = 2 if df.shape[1] > 2 else x_col
        y2_col = 3 if df.shape[1] > 3 else y1_col
    else:
        x_col, y1_col, y2_col = 1, 2, 3

    x = pd.to_numeric(df.iloc[:, x_col], errors="coerce")
    y1 = pd.to_numeric(df.iloc[:, y1_col], errors="coerce")
    y2_raw = pd.to_numeric(df.iloc[:, y2_col], errors="coerce")

    mask = np.isfinite(x) & np.isfinite(y1) & np.isfinite(y2_raw)
    x = x[mask].astype(float)
    y1 = y1[mask].astype(float)
    y2_raw = y2_raw[mask].astype(float)

    if len(x) > 1:
        order = np.argsort(x)
        x = x[order]
        y1 = y1[order]
        y2_raw = y2_raw[order]

    y2 = -y2_raw

    weight_data = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(x, y1)]
    dtg_data = [[round(float(a), 3), round(float(b), 3)] for a, b in zip(x, y2)]

    x_max = max(200.0, ceil_to_step(float(np.max(x)), 200.0)) if len(x) > 0 else 1000.0
    y1_max = max(100.0, ceil_to_step(float(np.max(y1)), 20.0)) if len(y1) > 0 else 100.0

    if len(y2) > 0:
        y2_min_raw = float(np.min(y2))
        y2_max_raw = float(np.max(y2))
    else:
        y2_min_raw = -0.2
        y2_max_raw = 0.2

    y2_min = floor_to_step(y2_min_raw, 0.2)
    y2_max = ceil_to_step(y2_max_raw, 0.2)

    if y2_min > 0:
        y2_min = 0.0
    if y2_max < 0:
        y2_max = 0.0
    if y2_max <= y2_min:
        y2_max = y2_min + 0.2

    y2_min = round(y2_min, 1)
    y2_max = round(y2_max, 1)

    if abs(y2_min) < 1e-9:
        y2_min = 0.0
    if abs(y2_max) < 1e-9:
        y2_max = 0.0

    residue_label = None
    residue_coord = None
    if len(x) > 0:
        residue_idx = int(np.argmin(np.abs(x - 800.0)))
        residue_temp = float(x[residue_idx])
        residue_weight = float(y1[residue_idx])
        residue_label = f"Residue {residue_weight:.1f}%"
        residue_coord = [round(residue_temp, 3), round(residue_weight, 3)]

    peak_label = None
    peak_coord = None
    if len(x) > 0:
        above_150 = np.where(x > 150.0)[0]
        if len(above_150) == 0:
            above_150 = np.arange(len(x))

        peak_idx = int(above_150[int(np.argmax(y2[above_150]))])
        peak_temp = float(x[peak_idx])
        peak_value = float(y2[peak_idx])

        peak_label = f"{peak_temp:.0f} °C\nMax {peak_value:.2f}"
        peak_coord = [round(peak_temp, 3), round(peak_value, 3)]

    font = "Noto Sans CJK KR"

    weight_mark_data = []
    if residue_coord is not None:
        weight_mark_data.append({
            "coord": residue_coord,
            "label": {
                "show": True,
                "position": "top",
                "formatter": residue_label,
                "color": "#1f4e9c",
                "fontSize": 12,
                "fontFamily": font
            }
        })

    dtg_mark_data = []
    if peak_coord is not None:
        dtg_mark_data.append({
            "coord": peak_coord,
            "label": {
                "show": True,
                "position": "top",
                "formatter": peak_label,
                "color": "#c0392b",
                "fontSize": 12,
                "fontFamily": font
            }
        })

    option = {
        "backgroundColor": "#ffffff",
        "animation": False,
        "textStyle": {
            "fontFamily": font,
            "fontSize": 12
        },
        "title": {
            "text": str(actual_sheet),
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontSize": 16,
                "fontFamily": font
            }
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "legend": {
            "data": ["Weight", "Deriv.Weight"],
            "left": "left",
            "top": "middle",
            "orient": "vertical"
        },
        "grid": {
            "left": 80,
            "right": 80,
            "top": 60,
            "bottom": 60
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 30,
            "min": 0.0,
            "max": float(x_max),
            "interval": 200,
            "axisTick": {"show": True},
            "axisLabel": {"formatter": "{value}"},
            "splitLine": {"show": True}
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 45,
                "min": 0.0,
                "max": float(y1_max),
                "interval": 20,
                "axisTick": {"show": True},
                "axisLabel": {"formatter": "{value}"},
                "splitLine": {"show": True}
            },
            {
                "type": "value",
                "name": "Deriv.Weight (%/°C)",
                "nameLocation": "middle",
                "nameGap": 45,
                "min": float(y2_min),
                "max": float(y2_max),
                "interval": 0.2,
                "axisTick": {"show": True},
                "axisLabel": {"formatter": "{value}"},
                "splitLine": {"show": False}
            }
        ],
        "series": [
            {
                "name": "Weight",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "lineStyle": {
                    "color": "#1f4e9c",
                    "width": 1.5
                },
                "itemStyle": {
                    "color": "#1f4e9c"
                },
                "data": weight_data,
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {
                        "color": "#1f4e9c",
                        "borderColor": "#ffffff",
                        "borderWidth": 1
                    },
                    "label": {
                        "show": True,
                        "position": "top",
                        "fontSize": 12,
                        "fontFamily": font
                    },
                    "data": weight_mark_data
                }
            },
            {
                "name": "Deriv.Weight",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {
                    "color