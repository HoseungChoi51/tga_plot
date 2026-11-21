import json
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

def column_by_name(df, pattern):
    for col in df.columns:
        if re.search(pattern, str(col), re.IGNORECASE):
            return col
    raise ValueError(f"Could not find column matching {pattern!r}")

def main():
    df = pd.read_excel(DATA_FILE, sheet_name=1)
    temp_col = column_by_name(df, r"Temperature")
    weight_col = column_by_name(df, r"Weight\s*\(%\)")

    data = df[[temp_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(temp_col)
    temperatures = data[temp_col].to_numpy(dtype=float)
    weights = data[weight_col].to_numpy(dtype=float)

    def weight_at(target):
        return float(np.interp(target, temperatures, weights))

    markers = []
    for target in (300, 600):
        value = weight_at(target)
        markers.append({
            "name": f"{target} °C",
            "coord": [target, value],
            "value": f"{value:.2f}%",
            "label": {
                "show": True,
                "formatter": f"{target} °C: {value:.2f}%",
                "position": "top",
                "distance": 10,
                "fontSize": 13,
                "fontWeight": "bold",
                "color": "#333333",
                "backgroundColor": "rgba(255,255,255,0.88)",
                "padding": [4, 6],
                "borderRadius": 3,
            },
        })

    option = {
        "animation": False,
        "backgroundColor": "#ffffff",
        "title": {
            "text": str(pd.ExcelFile(DATA_FILE).sheet_names[1]),
            "left": "center",
            "top": 12,
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            "valueFormatter": "{value}",
        },
        "grid": {"left": 78, "right": 35, "top": 70, "bottom": 68},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 42,
            "min": 30,
            "max": 900,
            "axisLine": {"lineStyle": {"color": "#555555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 13},
            "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 54,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 13},
            "splitLine": {"show": True, "lineStyle": {"color": "#e8e8e8"}},
        },
        "series": [{
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2.5, "color": "#2f6b9a"},
            "itemStyle": {"color": "#2f6b9a"},
            "data": [[float(x), float(y)] for x, y in zip(temperatures, weights)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 11,
                "itemStyle": {"color": "#d9534f", "borderColor": "#ffffff", "borderWidth": 2},
                "data": markers,
            },
            "markLine": {
                "silent": True,
                "symbol": ["none", "none"],
                "lineStyle": {"color": "#d9534f", "type": "dashed", "width": 1.5, "opacity": 0.75},
                "label": {"show": False},
                "data": [{"xAxis": 300}, {"xAxis": 600}],
            },
        }],
    }

    print(json.dumps({
        "figures": [{
            "name": "second_sheet_weight",
            "option": option,
            "width": 800,
            "height": 520,
            "dpi": 300,
            "formats": ["png"],
        }]
    }, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
