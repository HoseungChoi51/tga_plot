import json
import os
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

colors = ["#5470C6", "#91CC75", "#FAC858"]
figures = []

excel = pd.ExcelFile(DATA_FILE)
for index, sheet in enumerate(excel.sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    temp_col = next((c for c in df.columns if "temperature" in c.lower()), df.columns[1])
    weight_col = next((c for c in df.columns if "weight" in c.lower()), df.columns[2])
    deriv_col = next((c for c in df.columns if "d.w" in c.lower() or "deriv" in c.lower()), None)

    temp = pd.to_numeric(df[temp_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid = temp.notna() & weight.notna()
    x = temp[valid].tolist()
    y = weight[valid].tolist()

    series = [{
        "name": "Weight(%)",
        "type": "line",
        "data": [[float(a), float(b)] for a, b in zip(x, y)],
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": colors[index % len(colors)]},
        "itemStyle": {"color": colors[index % len(colors)]},
        "markArea": {
            "silent": True,
            "itemStyle": {"color": "rgba(180, 180, 180, 0.22)"},
            "data": [[{"xAxis": 300}, {"xAxis": 450}]],
        },
    }]

    if deriv_col is not None:
        deriv = pd.to_numeric(df[deriv_col], errors="coerce")
        valid_d = temp.notna() & deriv.notna()
        series.append({
            "name": "D.W(%/C)",
            "type": "line",
            "yAxisIndex": 1,
            "data": [[float(a), float(b)] for a, b in zip(temp[valid_d], deriv[valid_d])],
            "showSymbol": False,
            "lineStyle": {"width": 1.5, "color": "#EE6666"},
            "itemStyle": {"color": "#EE6666"},
        })

    option = {
        "animation": False,
        "title": {
            "text": sheet,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 30},
        "grid": {"left": 72, "right": 76 if deriv_col else 32, "top": 74, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": 30,
            "max": float(temp.max()),
            "axisLine": {"lineStyle": {"color": "#555"}},
            "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 48,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": "#555"}},
                "splitLine": {"lineStyle": {"color": "#e8e8e8"}},
            }
        ],
        "series": series,
    }

    if deriv_col is not None:
        option["yAxis"].append({
            "type": "value",
            "name": "D.W (%/°C)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLine": {"show": True, "lineStyle": {"color": "#555"}},
            "splitLine": {"show": False},
        })

    figures.append({
        "name": f"tga_{index + 1}",
        "option": option,
        "width": 900,
        "height": 560,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
