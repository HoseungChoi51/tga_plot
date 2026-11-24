import json
import os
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
SHEET_NAME = "PVC"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_column(keywords):
    for col in df.columns:
        name = col.lower()
        if any(word in name for word in keywords):
            return col
    raise ValueError(f"필요한 열을 찾을 수 없습니다: {keywords}")

x_col = find_column(["temperature", "temp", "온도"])
weight_col = find_column(["weight", "mass", "무게", "질량"])
dtg_col = find_column(["deriv", "dtg", "미분"])

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(x_col)

def weight_at_temperature(temp):
    # 해당 온도에서의 질량을 선형 보간
    return float(np.interp(temp, data[x_col].to_numpy(), data[weight_col].to_numpy()))

w200 = weight_at_temperature(200.0)
w400 = weight_at_temperature(400.0)
mass_loss = w200 - w400

# 표시용 선 데이터
x = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

# DTG는 질량 감소 피크가 위로 향하도록 부호 반전
dtg_plot = -dtg
peak_mask = x > 150
peak_idx = int(np.argmax(np.where(peak_mask, dtg_plot, -np.inf)))
peak_x = float(x[peak_idx])
peak_y = float(dtg_plot[peak_idx])

residue_idx = int(np.argmin(np.abs(x - 800.0)))
residue_x = float(x[residue_idx])
residue_y = float(weight[residue_idx])

option = {
    "animation": False,
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight (%)", "DTG (-%/°C)"], "left": "center"},
    "grid": {"left": 72, "right": 72, "top": 80, "bottom": 65},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 35,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
        },
        {
            "type": "value",
            "name": "DTG (-%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "Weight (%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "data": [
                    {
                        "name": f"Residue {residue_y:.1f}%",
                        "coord": [residue_x, residue_y],
                        "label": {"formatter": f"Residue {residue_y:.1f}%", "position": "right"}
                    }
                ]
            },
            "markLine": {
                "symbol": ["none", "none"],
                "lineStyle": {"color": "#555555", "type": "dashed", "width": 1},
                "label": {"show": False},
                "data": [
                    {"xAxis": 200},
                    {"xAxis": 400}
                ]
            }
        },
        {
            "name": "DTG (-%/°C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 1.8},
            "data": [[float(a), float(b)] for a, b in zip(x, dtg_plot)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "data": [
                    {
                        "name": f"{peak_x:.0f} °C",
                        "coord": [peak_x, peak_y],
                        "label": {"formatter": f"{peak_x:.0f} °C", "position": "top"}
                    }
                ]
            }
        },
        {
            "name": "Mass loss annotation",
            "type": "line",
            "yAxisIndex": 0,
            "silent": True,
            "showSymbol": False,
            "lineStyle": {"opacity": 0},
            "data": [],
            "markArea": {
                "silent": True,
                "itemStyle": {"color": "rgba(243, 156, 18, 0.12)"},
                "label": {
                    "show": True,
                    "position": "insideTop",
                    "color": "#8a4b08",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 13,
                    "formatter": f"200–400 °C 질량 감소량: {mass_loss:.2f}%"
                },
                "data": [[{"xAxis": 200}, {"xAxis": 400}]]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "PVC_mass_loss_200_400C",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
