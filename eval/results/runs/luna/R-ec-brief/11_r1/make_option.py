import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def clean_name(value):
    name = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", str(value)).strip("_")
    return name or "plot"


def main():
    workbook = pd.ExcelFile(DATA_FILE)
    figures = []

    for sheet_name in workbook.sheet_names:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        if df.empty or len(df.columns) < 4:
            continue

        lower_names = [str(c).strip().lower() for c in df.columns]

        def find_col(candidates, fallback):
            for candidate in candidates:
                for i, name in enumerate(lower_names):
                    if candidate in name:
                        return i
            return fallback

        x_idx = find_col(["temperature", "temp"], 1)
        weight_idx = find_col(["weight"], 2)
        dtg_idx = find_col(["d.w", "dtg", "derivative"], 3)

        x = pd.to_numeric(df.iloc[:, x_idx], errors="coerce")
        weight = pd.to_numeric(df.iloc[:, weight_idx], errors="coerce")
        dtg = pd.to_numeric(df.iloc[:, dtg_idx], errors="coerce")
        valid = x.notna() & weight.notna() & dtg.notna()
        x = x[valid].to_numpy(dtype=float)
        weight = weight[valid].to_numpy(dtype=float)
        dtg = dtg[valid].to_numpy(dtype=float)
        if not len(x):
            continue

        residue_idx = int(np.argmin(np.abs(x - 800)))
        residue_x = float(x[residue_idx])
        residue_y = float(weight[residue_idx])

        weight_data = [[float(a), float(b)] for a, b in zip(x, weight)]
        dtg_data = [[float(a), float(-b)] for a, b in zip(x, dtg)]

        option = {
            "animation": False,
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Weight(%)", "-DTG(%/°C)"],
                "left": "center",
                "top": 32,
                "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            },
            "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": float(np.nanmin(x)),
                "max": float(np.nanmax(x)),
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
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
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
                },
            ],
            "series": [
                {
                    "name": "Weight(%)",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 0,
                    "data": weight_data,
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "itemStyle": {"color": "#1f4e9c"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "data": [{
                            "coord": [residue_x, residue_y],
                            "name": f"Residue {residue_y:.1f}%",
                            "label": {
                                "show": True,
                                "formatter": f"Residue {residue_y:.1f}%",
                                "position": "top",
                                "fontFamily": "Noto Sans CJK KR",
                            },
                            "itemStyle": {"color": "#1f4e9c"},
                        }],
                    },
                },
                {
                    "name": "-DTG(%/°C)",
                    "type": "line",
                    "showSymbol": False,
                    "yAxisIndex": 1,
                    "data": dtg_data,
                    "lineStyle": {"color": "#c0392b", "width": 1.8},
                    "itemStyle": {"color": "#c0392b"},
                },
            ],
        }

        figures.append({
            "name": clean_name(sheet_name),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
