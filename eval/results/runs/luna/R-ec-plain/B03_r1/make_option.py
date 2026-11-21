import json
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"

df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

x_col = "Angular frequency (rad/s)"
g1_col = "Storage modulus G' (Pa)"
g2_col = "Loss modulus G'' (Pa)"

data_g1 = []
data_g2 = []
for _, row in df.iterrows():
    try:
        x = float(row[x_col])
        g1 = float(row[g1_col])
        g2 = float(row[g2_col])
    except (TypeError, ValueError):
        continue
    if x > 0 and g1 > 0 and g2 > 0:
        data_g1.append([x, g1])
        data_g2.append([x, g2])

option = {
    "animation": False,
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "legend": {
        "data": ["저장 탄성률 G′", "손실 탄성률 G″"],
        "top": 10
    },
    "grid": {
        "left": 75,
        "right": 75,
        "top": 55,
        "bottom": 65
    },
    "xAxis": {
        "type": "log",
        "name": "각주파수 (rad/s)",
        "nameLocation": "middle",
        "nameGap": 42,
        "logBase": 10,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "yAxis": [
        {
            "type": "log",
            "name": "G′ (Pa)",
            "nameLocation": "middle",
            "nameGap": 55,
            "logBase": 10,
            "axisLine": {"show": True, "lineStyle": {"color": "#2563eb"}},
            "axisLabel": {"color": "#2563eb"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
        },
        {
            "type": "log",
            "name": "G″ (Pa)",
            "nameLocation": "middle",
            "nameGap": 55,
            "logBase": 10,
            "axisLine": {"show": True, "lineStyle": {"color": "#dc2626"}},
            "axisLabel": {"color": "#dc2626"},
            "splitLine": {"show": False}
        }
    ],
    "series": [
        {
            "name": "저장 탄성률 G′",
            "type": "line",
            "yAxisIndex": 0,
            "data": data_g1,
            "showSymbol": True,
            "symbol": "circle",
            "symbolSize": 6,
            "lineStyle": {"width": 2, "color": "#2563eb"},
            "itemStyle": {"color": "#2563eb"}
        },
        {
            "name": "손실 탄성률 G″",
            "type": "line",
            "yAxisIndex": 1,
            "data": data_g2,
            "showSymbol": True,
            "symbol": "circle",
            "symbolSize": 6,
            "lineStyle": {"width": 2, "color": "#dc2626"},
            "itemStyle": {"color": "#dc2626"}
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "rheology_moduli_vs_frequency",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False))
