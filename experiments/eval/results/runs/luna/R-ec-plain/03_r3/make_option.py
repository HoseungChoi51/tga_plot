import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V acid"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
derivative = derivative[valid].to_numpy()

# Mark the two strongest DTG mass-loss peaks (most negative derivative).
local_minima = [
    i for i in range(1, len(derivative) - 1)
    if derivative[i] <= derivative[i - 1] and derivative[i] < derivative[i + 1]
]
if len(local_minima) < 2:
    local_minima = list(range(len(derivative)))

peak_indices = sorted(
    sorted(local_minima, key=lambda i: derivative[i])[:2],
    key=lambda i: temperature[i],
)

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "title": {
        "text": "1006R1-V acid",
        "left": "center",
        "top": 12,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "bold"},
    },
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
    "legend": {"data": ["Weight(%)", "D.W(%/C)"], "top": 42},
    "grid": {"left": 78, "right": 82, "top": 88, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "min": 100,
        "max": 800,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "min": 0,
            "max": 105,
            "axisLine": {"show": True, "lineStyle": {"color": "#2563a6"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#2563a6"},
            "splitLine": {"lineStyle": {"color": "#e8edf2"}},
        },
        {
            "type": "value",
            "name": "D.W (%/°C)",
            "axisLine": {"show": True, "lineStyle": {"color": "#d35400"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#d35400"},
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
            "lineStyle": {"width": 2, "color": "#2563a6"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
        },
        {
            "name": "D.W(%/C)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "smooth": False,
            "lineStyle": {"width": 2, "color": "#d35400"},
            "data": [[float(x), float(y)] for x, y in zip(temperature, derivative)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 12,
                "itemStyle": {"color": "#c0392b", "borderColor": "#ffffff", "borderWidth": 2},
                "label": {
                    "show": True,
                    "formatter": "{b}\n{c}",
                    "fontFamily": "Noto Sans CJK KR",
                    "fontSize": 11,
                    "position": "top",
                },
                "data": [
                    {
                        "name": f"피크 {rank}: {temperature[i]:.1f}°C",
                        "coord": [float(temperature[i]), float(derivative[i])],
                        "value": float(derivative[i]),
                    }
                    for rank, i in enumerate(peak_indices, start=1)
                ],
            },
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "1006R1-V_acid",
        "option": option,
        "width": 900,
        "height": 600,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
