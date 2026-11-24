import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

colors = ["#2878B5", "#D9534F", "#3A9D5D"]
figures = []

for idx, (sheet, color) in enumerate(zip(
    ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"], colors
)):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next(c for c in df.columns if "temperature" in c.lower())
    weight_col = next(c for c in df.columns if "weight" in c.lower())
    derivative_col = next(c for c in df.columns if "d.w" in c.lower() or "dw" in c.lower())

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    derivative = pd.to_numeric(df[derivative_col], errors="coerce")

    valid = temperature.notna() & weight.notna() & derivative.notna()
    temp_values = temperature[valid].tolist()
    weight_values = weight[valid].tolist()
    derivative_values = derivative[valid].tolist()

    figures.append({
        "name": f"tga_{idx + 1}",
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
        "option": {
            "animation": False,
            "backgroundColor": "#ffffff",
            "title": {
                "text": sheet,
                "left": "center",
                "top": 12,
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18}
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "cross"}
            },
            "legend": {
                "data": ["Weight (%)", "D.W (%/°C)"],
                "top": 44,
                "textStyle": {"fontFamily": "Noto Sans CJK KR"}
            },
            "grid": {"left": 76, "right": 78, "top": 92, "bottom": 68},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 38,
                "min": 30,
                "max": 900 if "750C" not in sheet else 750,
                "axisLine": {"lineStyle": {"color": "#555555"}},
                "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                "splitLine": {"show": True, "lineStyle": {"color": "#eeeeee"}}
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "min": 0,
                    "max": 105,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"lineStyle": {"color": "#eeeeee"}}
                },
                {
                    "type": "value",
                    "name": "D.W (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 52,
                    "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
                    "splitLine": {"show": False}
                }
            ],
            "series": [
                {
                    "name": "Weight (%)",
                    "type": "line",
                    "showSymbol": False,
                    "smooth": False,
                    "yAxisIndex": 0,
                    "data": [[x, y] for x, y in zip(temp_values, weight_values)],
                    "lineStyle": {"width": 2, "color": color},
                    "itemStyle": {"color": color},
                    "markArea": {
                        "silent": True,
                        "itemStyle": {"color": "rgba(150, 150, 150, 0.18)"},
                        "data": [[{"xAxis": 300}, {"xAxis": 450}]]
                    }
                },
                {
                    "name": "D.W (%/°C)",
                    "type": "line",
                    "showSymbol": False,
                    "smooth": False,
                    "yAxisIndex": 1,
                    "data": [[x, y] for x, y in zip(temp_values, derivative_values)],
                    "lineStyle": {"width": 1.7, "color": "#555555"},
                    "itemStyle": {"color": "#555555"}
                }
            ]
        }
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
