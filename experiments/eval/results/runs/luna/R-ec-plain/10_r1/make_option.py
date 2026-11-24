import json
import os
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

SHEETS = [
    ("1006R1-V normal", "Normal"),
    ("1006R1-V acid", "Acid"),
    ("1006R1-V 750C", "750 °C"),
]
TARGET_TEMPERATURE = 700.0


def load_sheet(path, sheet_name):
    df = pd.read_excel(path, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = next(c for c in df.columns if "temperature" in c.lower())
    y_col = next(c for c in df.columns if "weight" in c.lower())
    data = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
    return data[x_col].to_numpy(dtype=float), data[y_col].to_numpy(dtype=float)


def value_at_temperature(temperatures, weights, target):
    order = np.argsort(temperatures)
    temperatures = temperatures[order]
    weights = weights[order]
    return float(np.interp(target, temperatures, weights))


def main():
    path = os.environ.get("DATA_FILE", DATA_FILE)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    series = []
    residues = []

    for sheet, label in SHEETS:
        temperatures, weights = load_sheet(path, sheet)
        residue = value_at_temperature(temperatures, weights, TARGET_TEMPERATURE)
        residues.append({"name": label, "value": residue})
        series.append({
            "name": label,
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2.2},
            "data": [[float(x), float(y)] for x, y in zip(temperatures, weights)],
            "markLine": {
                "symbol": ["none", "none"],
                "silent": True,
                "lineStyle": {"type": "dashed", "width": 1.2, "color": "#777"},
                "label": {"show": False},
                "data": [{"xAxis": TARGET_TEMPERATURE}],
            },
        })

    residue_text = "   ·   ".join(
        f"{item['name']} {item['value']:.2f}%" for item in residues
    )

    option = {
        "animation": False,
        "title": {
            "text": "TGA 열중량 분석",
            "subtext": f"700 °C 잔류량: {residue_text}",
            "left": "center",
            "top": 10,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"},
            "subtextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12, "color": "#444"},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "line"},
            "valueFormatter": "{value}%",
        },
        "legend": {
            "data": [label for _, label in SHEETS],
            "top": 67,
            "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        },
        "grid": {"left": 76, "right": 28, "top": 110, "bottom": 70},
        "xAxis": {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 42,
            "min": 30,
            "max": 900,
            "axisLine": {"lineStyle": {"color": "#555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
        },
        "yAxis": {
            "type": "value",
            "name": "중량 (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 105,
            "axisLine": {"lineStyle": {"color": "#555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
        },
        "series": series,
    }

    print(json.dumps({
        "figures": [{
            "name": "tga_residue_700C",
            "option": option,
            "width": 900,
            "height": 560,
            "dpi": 300,
            "formats": ["png"],
        }]
    }, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
