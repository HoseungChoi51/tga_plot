import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

COLORS = ["#2563eb", "#dc2626", "#059669"]
WIDTH = 900
HEIGHT = 620

def clean_values(series):
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)

def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_index, sheet_name in enumerate(workbook.sheet_names):
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        temperature_col = next((c for c in df.columns if "temperature" in c.lower()), None)
        weight_col = next((c for c in df.columns if "weight" in c.lower()), None)
        derivative_col = next(
            (c for c in df.columns if "d.w" in c.lower() or "derivative" in c.lower()),
            None,
        )
        if temperature_col is None or weight_col is None or derivative_col is None:
            continue

        temperature = clean_values(df[temperature_col])
        weight = clean_values(df[weight_col])
        derivative = clean_values(df[derivative_col])
        valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(derivative)
        temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]
        if temperature.size == 0:
            continue

        # Preserve the measured points while reducing output size for rendering.
        max_points = 1800
        stride = max(1, int(np.ceil(temperature.size / max_points)))
        indices = np.arange(0, temperature.size, stride)
        if indices[-1] != temperature.size - 1:
            indices = np.append(indices, temperature.size - 1)

        name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(sheet_name)).strip("_") or f"tga_{sheet_index + 1}"
        option = {
            "backgroundColor": "#ffffff",
            "animation": False,
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "top": 12,
                "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "fontSize": 18, "fontWeight": "bold", "color": "#1f2937"},
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
                "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
            },
            "legend": {
                "top": 44,
                "data": ["Weight (%)", "D.W (%/°C)"],
                "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#374151"},
            },
            "grid": {"left": 82, "right": 82, "top": 88, "bottom": 74},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": float(np.nanmin(temperature)),
                "max": float(np.nanmax(temperature)),
                "axisLine": {"lineStyle": {"color": "#6b7280"}},
                "axisLabel": {"color": "#374151"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": "#374151"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "min": 0,
                    "max": 105,
                    "axisLine": {"show": True, "lineStyle": {"color": COLORS[0]}},
                    "axisLabel": {"color": COLORS[0]},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": COLORS[0]},
                    "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
                },
                {
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 58,
                    "axisLine": {"show": True, "lineStyle": {"color": COLORS[1]}},
                    "axisLabel": {"color": COLORS[1]},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif", "color": COLORS[1]},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "yAxisIndex": 0,
                    "showSymbol": False,
                    "sampling": "lttb",
                    "lineStyle": {"width": 2, "color": COLORS[0]},
                    "data": [[float(temperature[i]), float(weight[i])] for i in indices],
                },
                {
                    "name": "D.W (%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "sampling": "lttb",
                    "lineStyle": {"width": 1.8, "color": COLORS[1]},
                    "data": [[float(temperature[i]), float(derivative[i])] for i in indices],
                },
            ],
        }

        figures.append({
            "name": name,
            "option": option,
            "width": WIDTH,
            "height": HEIGHT,
            "dpi": 300,
            "formats": ["png"],
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
