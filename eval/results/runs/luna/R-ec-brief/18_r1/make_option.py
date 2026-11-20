import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    return re.sub(r"[\r\n]+", " ", str(value)).strip()

def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet in workbook.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        if df.empty:
            continue

        columns = {str(c).strip().lower(): c for c in df.columns}

        def find_column(predicate, fallback_index):
            for lowered, original in columns.items():
                if predicate(lowered):
                    return original
            return df.columns[fallback_index] if len(df.columns) > fallback_index else None

        x_col = find_column(lambda n: "temperature" in n or "temp" in n, 1)
        weight_col = find_column(lambda n: "weight" in n and ("%" in n or "mass" in n), 2)
        dtg_col = find_column(
            lambda n: ("d.w" in n or "dtg" in n or "deriv" in n), 3
        )
        if x_col is None or weight_col is None or dtg_col is None:
            continue

        x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
        weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
        dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
        x, weight, dtg = x[valid], weight[valid], dtg[valid]
        if not len(x):
            continue

        order = np.argsort(x)
        x, weight, dtg = x[order], weight[order], dtg[order]

        residue_idx = int(np.argmin(np.abs(x - 800)))
        peak_candidates = np.flatnonzero(x > 150)
        peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])]) if len(peak_candidates) else None

        dtg_up = -dtg
        series = [
            {
                "name": clean_name(weight_col),
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 0,
                "lineStyle": {"color": "#1f4e9c", "width": 2},
                "data": [[float(a), float(b)] for a, b in zip(x, weight)],
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": "#1f4e9c"},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {weight[residue_idx]:.1f}%",
                        "position": "top",
                    },
                    "data": [{"coord": [float(x[residue_idx]), float(weight[residue_idx])]}],
                },
            },
            {
                "name": clean_name(dtg_col) + " (-DTG)",
                "type": "line",
                "showSymbol": False,
                "yAxisIndex": 1,
                "lineStyle": {"color": "#c0392b", "width": 2},
                "data": [[float(a), float(b)] for a, b in zip(x, dtg_up)],
            },
        ]

        if peak_idx is not None:
            series[1]["markPoint"] = {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{x[peak_idx]:.0f} °C",
                    "position": "top",
                },
                "data": [{"coord": [float(x[peak_idx]), float(dtg_up[peak_idx])]}],
            }

        option = {
            "title": {"text": clean_name(sheet), "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"data": [clean_name(weight_col), clean_name(dtg_col) + " (-DTG)"], "left": "center"},
            "grid": {"left": 75, "right": 75, "top": 70, "bottom": 65},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 35,
                "min": float(np.nanmin(x)),
                "max": float(np.nanmax(x)),
                "interval": 100,
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                    "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "min": -0.05,
                    "max": 1.2,
                    "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                    "splitLine": {"show": False},
                },
            ],
            "series": series,
        }

        figures.append(
            {
                "name": f"plot{len(figures) + 1}",
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
