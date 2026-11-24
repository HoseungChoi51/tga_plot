import json
import os

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_number(value):
    value = float(value)
    return value if np.isfinite(value) else None

def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        def find_column(words, fallback):
            for col in df.columns:
                if any(word.lower() in col.lower() for word in words):
                    return col
            return df.columns[fallback]

        x_col = find_column(["temperature", "temp"], 1)
        weight_col = find_column(["weight"], 2)
        dtg_col = find_column(["d.w", "dtg", "derivative"], 3)

        data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        temperatures = data[x_col].to_numpy(dtype=float)
        weights = data[weight_col].to_numpy(dtype=float)
        dtg = data[dtg_col].to_numpy(dtype=float)

        residue_index = int(np.argmin(np.abs(temperatures - 800)))
        residue_x = temperatures[residue_index]
        residue_y = weights[residue_index]

        peak_candidates = np.flatnonzero(temperatures > 150)
        peak_index = int(peak_candidates[np.argmax(-dtg[peak_candidates])]) if len(peak_candidates) else int(np.argmax(-dtg))
        peak_x = temperatures[peak_index]
        peak_y = -dtg[peak_index]

        option = {
            "animation": False,
            "title": {
                "text": sheet_name,
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
            },
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Weight(%)", "-DTG(%/°C)"], "left": 15, "top": "middle", "orient": "vertical"},
            "grid": {"left": 80, "right": 80, "top": 65, "bottom": 65},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "splitLine": {"show": False}
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {"show": False}
                }
            ],
            "series": [
                {
                    "name": "Weight(%)",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "itemStyle": {"color": "#1f4e9c"},
                    "data": [[clean_number(x), clean_number(y)] for x, y in zip(temperatures, weights)],
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 8,
                        "itemStyle": {"color": "#1f4e9c"},
                        "label": {
                            "show": True,
                            "formatter": f"Residue {residue_y:.1f}%",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR"
                        },
                        "data": [{"coord": [clean_number(residue_x), clean_number(residue_y)]}]
                    },
                    "markLine": {
                        "symbol": ["none", "none"],
                        "silent": True,
                        "lineStyle": {"color": "#666666", "type": "dashed", "width": 1.5},
                        "label": {
                            "show": True,
                            "formatter": "산화 시작",
                            "position": "insideEndTop",
                            "fontFamily": "Noto Sans CJK KR"
                        },
                        "data": [{"xAxis": 450}]
                    }
                },
                {
                    "name": "-DTG(%/°C)",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "lineStyle": {"color": "#c0392b", "width": 2},
                    "itemStyle": {"color": "#c0392b"},
                    "data": [[clean_number(x), clean_number(-y)] for x, y in zip(temperatures, dtg)],
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 8,
                        "itemStyle": {"color": "#c0392b"},
                        "label": {
                            "show": True,
                            "formatter": f"{peak_x:.0f} °C",
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR"
                        },
                        "data": [{"coord": [clean_number(peak_x), clean_number(peak_y)]}]
                    }
                }
            ]
        }

        figures.append({
            "name": f"plot{len(figures) + 1}",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
