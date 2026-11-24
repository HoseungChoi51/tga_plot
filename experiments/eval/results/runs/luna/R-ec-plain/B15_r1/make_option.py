import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

book = pd.ExcelFile(DATA_FILE)
series = []
for sheet in book.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

    data = []
    for x, y in zip(pd.to_numeric(df[temperature_col], errors="coerce"),
                    pd.to_numeric(df[weight_col], errors="coerce")):
        if pd.notna(x) and pd.notna(y):
            data.append([float(x), float(y)])

    series.append({
        "name": str(sheet),
        "type": "line",
        "showSymbol": False,
        "smooth": False,
        "data": data,
        "lineStyle": {"width": 2},
        "emphasis": {"focus": "series"},
    })

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR, sans-serif"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": [s["name"] for s in series],
        "orient": "vertical",
        "right": 18,
        "top": "middle",
    },
    "grid": {
        "left": 75,
        "right": 135,
        "top": 45,
        "bottom": 65,
        "containLabel": False,
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e5e7eb"}},
    },
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "polymers_weight",
        "option": option,
        "width": 800,
        "height": 500,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
