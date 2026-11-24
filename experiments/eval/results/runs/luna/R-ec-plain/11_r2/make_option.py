import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_sheet_name(name):
    return re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", str(name)).strip("_") or "plot"


def main():
    excel = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_name in excel.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        if df.empty or len(df.columns) < 3:
            continue

        columns = {str(c).strip().lower(): c for c in df.columns}
        temperature_col = next(
            (c for k, c in columns.items() if "temperature" in k or "온도" in k),
            df.columns[1],
        )
        weight_col = next(
            (c for k, c in columns.items() if "weight" in k or "중량" in k),
            df.columns[2],
        )
        derivative_col = next(
            (c for k, c in columns.items() if "d.w" in k or "derivative" in k or "dw" in k),
            df.columns[3] if len(df.columns) > 3 else None,
        )

        temperature = pd.to_numeric(df[temperature_col], errors="coerce")
        weight = pd.to_numeric(df[weight_col], errors="coerce")
        valid = temperature.notna() & weight.notna()
        temperature = temperature[valid].to_numpy(dtype=float)
        weight = weight[valid].to_numpy(dtype=float)

        if not len(temperature):
            continue

        series = [{
            "name": "Weight",
            "type": "line",
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#2563eb"},
            "itemStyle": {"color": "#2563eb"},
            "yAxisIndex": 0,
            "emphasis": {"disabled": True},
        }]

        y_axes = [{
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 105,
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
        }]

        if derivative_col is not None:
            derivative = pd.to_numeric(df[derivative_col], errors="coerce")
            valid_derivative = pd.to_numeric(df[temperature_col], errors="coerce").notna() & derivative.notna()
            dx = pd.to_numeric(df.loc[valid_derivative, temperature_col], errors="coerce").to_numpy(dtype=float)
            dy = derivative[valid_derivative].to_numpy(dtype=float)
            if len(dx):
                series.append({
                    "name": "D.W",
                    "type": "line",
                    "data": [[float(x), float(y)] for x, y in zip(dx, dy)],
                    "showSymbol": False,
                    "symbol": "none",
                    "lineStyle": {"width": 1.8, "color": "#dc2626"},
                    "itemStyle": {"color": "#dc2626"},
                    "yAxisIndex": 1,
                    "emphasis": {"disabled": True},
                })
                finite_dy = dy[np.isfinite(dy)]
                if len(finite_dy):
                    lo, hi = float(np.min(finite_dy)), float(np.max(finite_dy))
                    padding = max((hi - lo) * 0.08, 0.02)
                    y_axes.append({
                        "type": "value",
                        "name": "D.W (%/°C)",
                        "min": lo - padding,
                        "max": hi + padding,
                        "nameLocation": "middle",
                        "nameGap": 52,
                        "axisLine": {"show": True},
                        "splitLine": {"show": False},
                    })

        option = {
            "animation": False,
            "backgroundColor": "#ffffff",
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "top": 10,
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16, "fontWeight": "normal"},
            },
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
            "legend": {"top": 36, "data": [s["name"] for s in series]},
            "grid": {"left": 78, "right": 82 if len(y_axes) > 1 else 30, "top": 82, "bottom": 62},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 36,
                "min": float(np.nanmin(temperature)),
                "max": float(np.nanmax(temperature)),
                "axisLine": {"show": True},
                "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
            },
            "yAxis": y_axes,
            "series": series,
        }

        figures.append({
            "name": clean_sheet_name(sheet_name),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
