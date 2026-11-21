import json
import os
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def json_safe(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
        return value if np.isfinite(value) else None
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    return value


def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet in workbook.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]

        def find_col(candidates):
            for col in df.columns:
                normalized = col.lower().replace(" ", "")
                if any(candidate in normalized for candidate in candidates):
                    return col
            return None

        x_col = find_col(["temperature", "temp"])
        y1_col = find_col(["weight(%)", "weight", "mass"])
        y2_col = find_col(["d.w", "dtg", "derivative"])

        if x_col is None or y1_col is None or y2_col is None:
            numeric = [c for c in df.columns if pd.to_numeric(df[c], errors="coerce").notna().any()]
            if len(numeric) < 3:
                continue
            x_col, y1_col, y2_col = numeric[:3]

        data = pd.DataFrame({
            "x": pd.to_numeric(df[x_col], errors="coerce"),
            "weight": pd.to_numeric(df[y1_col], errors="coerce"),
            "dtg": pd.to_numeric(df[y2_col], errors="coerce"),
        }).dropna()

        if data.empty:
            continue

        data = data.sort_values("x")
        x = data["x"].to_numpy(dtype=float)
        weight = data["weight"].to_numpy(dtype=float)
        dtg = data["dtg"].to_numpy(dtype=float)

        residue_idx = int(np.argmin(np.abs(x - 800)))
        residue_x = float(x[residue_idx])
        residue_y = float(weight[residue_idx])

        peak_mask = x > 150
        if peak_mask.any():
            peak_indices = np.flatnonzero(peak_mask)
            peak_idx = int(peak_indices[np.argmax(-dtg[peak_mask])])
            peak_x = float(x[peak_idx])
            peak_y = float(-dtg[peak_idx])
        else:
            peak_idx = int(np.argmax(-dtg))
            peak_x = float(x[peak_idx])
            peak_y = float(-dtg[peak_idx])

        x_values = [json_safe(v) for v in x]
        weight_values = [json_safe(v) for v in weight]
        dtg_values = [json_safe(v) for v in -dtg]

        option = {
            "title": {
                "text": str(sheet),
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Weight(%)", "-D.W(%/°C)"],
                "left": "center",
                "bottom": 8,
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "grid": {"left": 72, "right": 72, "top": 60, "bottom": 76},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 34,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": False},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
                },
                {
                    "type": "value",
                    "name": "-D.W (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": "Weight(%)",
                    "type": "line",
                    "yAxisIndex": 0,
                    "data": [[x_values[i], weight_values[i]] for i in range(len(x_values))],
                    "showSymbol": False,
                    "lineStyle": {"color": "#000000", "width": 2.5},
                    "itemStyle": {"color": "#000000"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 8,
                        "data": [
                            {
                                "coord": [json_safe(residue_x), json_safe(residue_y)],
                                "name": "Residue",
                                "label": {
                                    "show": True,
                                    "formatter": f"Residue {residue_y:.1f}%",
                                    "position": "top",
                                    "fontFamily": "Noto Sans CJK KR",
                                },
                            }
                        ],
                    },
                },
                {
                    "name": "-D.W(%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": [[x_values[i], dtg_values[i]] for i in range(len(x_values))],
                    "showSymbol": False,
                    "lineStyle": {"color": "#c0392b", "width": 1.5, "type": "dashed"},
                    "itemStyle": {"color": "#c0392b"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 8,
                        "data": [
                            {
                                "coord": [json_safe(peak_x), json_safe(peak_y)],
                                "name": "DTG peak",
                                "label": {
                                    "show": True,
                                    "formatter": f"{peak_x:.0f} °C",
                                    "position": "top",
                                    "fontFamily": "Noto Sans CJK KR",
                                },
                            }
                        ],
                    },
                },
            ],
        }

        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(sheet))
        figures.append({
            "name": safe_name or f"plot{len(figures) + 1}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
