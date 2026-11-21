import json
import math
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

df = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
deriv = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & deriv.notna()
temperature = temperature[valid].astype(float)
weight = weight[valid].astype(float)
deriv = deriv[valid].astype(float)

if temperature.empty:
    raise ValueError("시트에 유효한 Temperature, Weight, D.W 데이터가 없습니다.")

max_idx = deriv.idxmax()
max_temp = float(temperature.loc[max_idx])
max_deriv = float(deriv.loc[max_idx])

residue_idx = (temperature - 800).abs().idxmin()
residue_temp = float(temperature.loc[residue_idx])
residue_weight = float(weight.loc[residue_idx])

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "title": {
        "text": "1006R1-V normal TGA",
        "left": "center",
        "top": 10,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"}
    },
    "legend": {
        "data": ["Weight", "Deriv.Weight"],
        "top": 40,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {"left": 78, "right": 82, "top": 88, "bottom": 68},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"},
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 0,
        "max": 900,
        "interval": 200,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 100,
            "interval": 20,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "Deriv.Weight (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "min": -1.2,
            "max": 0.2,
            "interval": 0.2,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 0,
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "lineStyle": {"width": 2, "color": "#2369a8"},
            "markPoint": {
                "symbol": "pin",
                "symbolSize": 55,
                "data": [{
                    "name": f"Residue {residue_weight:.2f}%",
                    "coord": [residue_temp, residue_weight],
                    "value": f"Residue {residue_weight:.2f}%"
                }],
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_weight:.2f}%",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12
                },
                "itemStyle": {"color": "#2b8a3e"}
            }
        },
        {
            "name": "Deriv.Weight",
            "type": "line",
            "showSymbol": False,
            "yAxisIndex": 1,
            "data": [[float(x), float(y)] for x, y in zip(temperature, deriv)],
            "lineStyle": {"width": 2, "color": "#d1495b"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "data": [{
                    "name": "Max Deriv.Weight",
                    "coord": [max_temp, max_deriv],
                    "value": max_deriv
                }],
                "label": {
                    "show": True,
                    "formatter": f"Max {max_deriv:.4f} at {max_temp:.0f}°C",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 12
                },
                "itemStyle": {"color": "#d1495b"}
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_normal_TGA",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
