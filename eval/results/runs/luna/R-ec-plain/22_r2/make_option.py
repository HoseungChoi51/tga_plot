import json
import os
import pandas as pd
import numpy as np

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

figures = []
sheets = pd.read_excel(DATA_FILE, sheet_name=None)

colors = {
    "1006R1-V normal": "#5470C6",
    "1006R1-V acid": "#EE6666",
    "1006R1-V 750C": "#FAC858",
}

for sheet_name, df in sheets.items():
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={c: c.strip() for c in df.columns})

    required = ["Temperature", "Weight(%)", "D.W(%/C)"]
    if not all(col in df.columns for col in required):
        continue

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=required)

    x = df["Temperature"].to_numpy()
    weight = df["Weight(%)"].to_numpy()
    derivative = df["D.W(%/C)"].to_numpy()

    color = colors.get(sheet_name, "#5470C6")
    title = sheet_name

    option = {
        "backgroundColor": "#ffffff",
        "animation": False,
        "title": {
            "text": title,
            "left": "center",
            "top": 12,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 17,
                "fontWeight": "normal",
                "color": "#222222",
            },
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
        },
        "legend": {
            "data": ["Weight(%)", "D.W(%/C)"],
            "top": 43,
            "textStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12,
                "color": "#333333",
            },
        },
        "grid": {
            "left": 78,
            "right": 82,
            "top": 86,
            "bottom": 68,
        },
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": float(np.nanmax(x)),
            "axisLine": {"lineStyle": {"color": "#555555"}},
            "axisTick": {"show": True},
            "axisLabel": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 11,
                "color": "#333333",
            },
            "nameTextStyle": {
                "fontFamily": "Noto Sans CJK KR",
                "fontSize": 12,
                "color": "#333333",
            },
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": color}},
                "axisTick": {"show": True},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                    "color": color,
                },
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12,
                    "color": color,
                },
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "D.W (%/°C)",
                "nameLocation": "middle",
                "nameGap": 56,
                "axisLine": {"show": True, "lineStyle": {"color": "#008000"}},
                "axisTick": {"show": True, "lineStyle": {"color": "#008000"}},
                "axisLabel": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                    "color": "#008000",
                },
                "nameTextStyle": {
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12,
                    "color": "#008000",
                },
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Weight(%)",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {"width": 2, "color": color},
                "itemStyle": {"color": color},
                "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            },
            {
                "name": "D.W(%/C)",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "smooth": False,
                "lineStyle": {"width": 2, "color": "#008000"},
                "itemStyle": {"color": "#008000"},
                "data": [[float(a), float(b)] for a, b in zip(x, derivative)],
            },
        ],
    }

    safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in sheet_name).strip().replace(" ", "_")
    figures.append({
        "name": safe_name or "plot",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
