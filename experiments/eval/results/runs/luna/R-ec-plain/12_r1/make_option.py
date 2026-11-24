import json
import os
import sys

import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"


def main():
    figures = []
    sheets = [
        ("1006R1-V normal", "normal"),
        ("1006R1-V acid", "acid"),
        ("1006R1-V 750C", "750C"),
    ]
    colors = ["#277DA1", "#F3722C", "#43AA8B"]

    for sheet_name, suffix in sheets:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        x_col = next((c for c in df.columns if "temperature" in c.lower()), df.columns[1])
        weight_col = next((c for c in df.columns if "weight" in c.lower()), df.columns[2])
        derivative_col = next(
            (c for c in df.columns if "d.w" in c.lower() or "dw" in c.lower()),
            df.columns[3],
        )

        data = df[[x_col, weight_col, derivative_col]].apply(
            pd.to_numeric, errors="coerce"
        ).dropna()
        x = data[x_col].tolist()
        weight = data[weight_col].tolist()
        derivative = data[derivative_col].tolist()

        option = {
            "animation": False,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
            "title": {
                "text": f"TGA / DTG - {sheet_name}",
                "left": "center",
                "textStyle": {"fontSize": 18, "fontWeight": "bold"},
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"},
            },
            "legend": {
                "data": ["Weight (%)", "D.W (%/°C)"],
                "top": 36,
            },
            "grid": {"left": 72, "right": 76, "top": 86, "bottom": 66},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": 30,
                "max": 900 if sheet_name != "1006R1-V 750C" else 750,
                "axisLine": {"lineStyle": {"color": "#555555"}},
                "axisLabel": {"color": "#444444"},
                "splitLine": {"show": True, "lineStyle": {"color": "#E8E8E8"}},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "min": 0,
                    "max": 105,
                    "axisLine": {"show": True, "lineStyle": {"color": colors[0]}},
                    "axisLabel": {"color": colors[0]},
                    "splitLine": {"show": True, "lineStyle": {"color": "#E8E8E8"}},
                },
                {
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLine": {"show": True, "lineStyle": {"color": colors[1]}},
                    "axisLabel": {"color": colors[1]},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "showSymbol": False,
                    "smooth": False,
                    "lineStyle": {"width": 2, "color": colors[0]},
                    "itemStyle": {"color": colors[0]},
                    "data": [[xx, yy] for xx, yy in zip(x, weight)],
                    "markLine": {
                        "silent": True,
                        "symbol": ["none", "none"],
                        "label": {
                            "show": True,
                            "formatter": "산화 시작",
                            "position": "insideEndTop",
                            "color": "#B42318",
                            "fontSize": 13,
                            "fontWeight": "bold",
                            "backgroundColor": "#FFFFFF",
                            "padding": [3, 5],
                        },
                        "lineStyle": {
                            "color": "#D92D20",
                            "width": 2,
                            "type": "dashed",
                        },
                        "data": [{"xAxis": 450}],
                    },
                },
                {
                    "name": "D.W (%/°C)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "smooth": False,
                    "lineStyle": {"width": 1.8, "color": colors[1]},
                    "itemStyle": {"color": colors[1]},
                    "data": [[xx, yy] for xx, yy in zip(x, derivative)],
                },
            ],
        }

        figures.append(
            {
                "name": f"tga_{suffix}",
                "option": option,
                "width": 900,
                "height": 560,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
