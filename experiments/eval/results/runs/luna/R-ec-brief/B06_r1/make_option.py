import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"


def read_table(path):
    path = Path(path)
    try:
        df = pd.read_csv(path, sep=None, engine="python", comment="#")
        if df.shape[1] < 2:
            raise ValueError
    except Exception:
        df = pd.read_csv(path, sep=r"\s+", engine="python", comment="#")
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    return df


def numeric_column(df, pattern):
    for col in df.columns:
        if re.search(pattern, str(col), flags=re.I):
            values = pd.to_numeric(df[col], errors="coerce")
            if values.notna().sum():
                return values
    return None


df = read_table(DATA_FILE)
time = numeric_column(df, r"time")
weight = numeric_column(df, r"weight|mass")
temperature = numeric_column(df, r"temperature|temp")

if time is None or weight is None or temperature is None:
    # The supplied file preview indicates columns A=Time, B=Temperature, C=Weight.
    if df.shape[1] < 3:
        raise ValueError("Expected time, temperature, and weight columns.")
    time = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")

data = pd.DataFrame({"time": time, "weight": weight, "temperature": temperature}).dropna()
data = data.sort_values("time")

x = data["time"].to_numpy(dtype=float)
w = data["weight"].to_numpy(dtype=float)
t = data["temperature"].to_numpy(dtype=float)

idx = int(np.argmin(np.abs(x - 140.0)))
label = f"무게 {w[idx]:.2f}% (140분)"

option = {
    "title": {
        "text": "isothermal",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "animation": False,
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["무게 (%)", "온도 (°C)"],
        "left": "center",
        "bottom": 8,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "grid": {"left": 70, "right": 70, "top": 60, "bottom": 60},
    "xAxis": {
        "type": "value",
        "name": "시간 (분)",
        "nameLocation": "middle",
        "nameGap": 32,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "무게 (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#1f4e9c"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#c0392b"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "무게 (%)",
            "type": "line",
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, w)],
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "itemStyle": {"color": "#1f4e9c"},
            "yAxisIndex": 0,
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "data": [
                    {
                        "coord": [float(x[idx]), float(w[idx])],
                        "value": label,
                        "label": {
                            "show": True,
                            "formatter": label,
                            "position": "top",
                            "fontFamily": "Noto Sans CJK KR",
                        },
                    }
                ],
            },
        },
        {
            "name": "온도 (°C)",
            "type": "line",
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, t)],
            "lineStyle": {"width": 2, "color": "#c0392b"},
            "itemStyle": {"color": "#c0392b"},
            "yAxisIndex": 1,
        },
    ],
}

print(json.dumps({
    "figures": [{
        "name": "isothermal",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
