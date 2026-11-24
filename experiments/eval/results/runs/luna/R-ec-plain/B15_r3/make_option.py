import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"

# Plot the weight (%) curves from all three sheets against temperature.
colors = ["#2563eb", "#dc2626", "#16a34a"]
series = []

for sheet, color in zip(["PE", "PVC", "PET"], colors):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next(c for c in df.columns if "Temperature" in c)
    weight_col = next(c for c in df.columns if "Weight" in c and "Deriv" not in c)

    data = []
    for x, y in zip(df[temperature_col], df[weight_col]):
        if pd.notna(x) and pd.notna(y):
            data.append([float(x), float(y)])

    series.append({
        "name": sheet,
        "type": "line",
        "data": data,
        "showSymbol": False,
        "symbol": "none",
        "lineStyle": {"width": 2, "color": color},
        "itemStyle": {"color": color},
        "emphasis": {"focus": "series"},
        "clip": True,
    })

option = {
    "animation": False,
    "title": {
        "text": "TGA Weight Curves",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
    },
    "legend": {
        "data": ["PE", "PVC", "PET"],
        "orient": "vertical",
        "right": 12,
        "top": "middle",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 12},
    },
    "grid": {
        "left": 72,
        "right": 120,
        "top": 60,
        "bottom": 65,
        "containLabel": True,
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#e5e7eb"}},
    },
    "yAxis": {
        "type": "value",
        "name": "Weight (%)",
        "nameLocation": "middle",
        "nameGap": 50,
        "min": 0,
        "max": 105,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"lineStyle": {"color": "#e5e7eb"}},
    },
    "series": series,
}

result = {
    "figures": [{
        "name": "tga_weight_comparison",
        "option": option,
        "width": 800,
        "height": 500,
        "dpi": 300,
        "formats": ["png"],
    }]
}

print(json.dumps(result, ensure_ascii=False, allow_nan=False))
