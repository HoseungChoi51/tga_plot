import json
import re
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    name = re.sub(r"[^\w.-]+", "_", str(value).strip(), flags=re.UNICODE)
    return name.strip("_") or "plot"

def main():
    workbook = pd.read_excel(DATA_FILE, sheet_name=None)
    figures = []

    for sheet_name, df in workbook.items():
        df.columns = [str(column).strip() for column in df.columns]

        def find_column(candidates):
            for column in df.columns:
                if any(candidate in column.lower() for candidate in candidates):
                    return column
            return None

        temp_col = find_column(["temperature", "temp"])
        weight_col = find_column(["weight"])
        dtg_col = find_column(["d.w", "dtg", "derivative"])

        if temp_col is None or weight_col is None or dtg_col is None:
            continue

        data = df[[temp_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        temperatures = data[temp_col].to_numpy(dtype=float)
        weights = data[weight_col].to_numpy(dtype=float)
        dtg_up = -data[dtg_col].to_numpy(dtype=float)

        residue_index = int(np.argmin(np.abs(temperatures - 800.0)))
        residue_temp = float(temperatures[residue_index])
        residue_weight = float(weights[residue_index])

        peak_candidates = np.flatnonzero(temperatures > 150.0)
        if len(peak_candidates):
            peak_index = int(peak_candidates[np.argmax(dtg_up[peak_candidates])])
            peak_temp = float(temperatures[peak_index])
            peak_value = float(dtg_up[peak_index])
            peak_label = f"{peak_temp:.0f} °C"
        else:
            peak_index = None

        weight_series = {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 0,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "data": [[float(x), float(y)] for x, y in zip(temperatures, weights)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.1f}%",
                    "position": "right"
                },
                "data": [{"coord": [residue_temp, residue_weight]}]
            }
        }

        dtg_series = {
            "name": "DTG",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 1,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "data": [[float(x), float(y)] for x, y in zip(temperatures, dtg_up)]
        }
        if peak_index is not None:
            dtg_series["markPoint"] = {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": peak_label,
                    "position": "top"
                },
                "data": [{"coord": [peak_temp, peak_value]}]
            }

        option = {
            "title": {"text": str(sheet_name), "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Weight", "DTG"], "left": "center", "top": "middle"},
            "grid": {"left": 75, "right": 75, "top": 65, "bottom": 65},
            "xAxis": {
                "type": "value",
                "name": "온도 (°C)",
                "nameLocation": "middle",
                "nameGap": 35,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "axisLabel": {"show": True}
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "무게 (%)",
                    "nameLocation": "middle",
                    "nameGap": 50,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "axisLabel": {"show": True},
                    "splitLine": {"show": True}
                },
                {
                    "type": "value",
                    "name": "미분 무게 (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 55,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "axisLabel": {"show": True},
                    "splitLine": {"show": False}
                }
            ],
            "series": [weight_series, dtg_series]
        }

        figures.append({
            "name": clean_name(sheet_name),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
