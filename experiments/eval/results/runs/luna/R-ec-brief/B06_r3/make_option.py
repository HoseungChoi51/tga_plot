import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/isothermal.txt"


def read_text_table(path):
    # Try common delimiters and encodings, then fall back to automatic parsing.
    for encoding in ("utf-8-sig", "cp949", "latin1"):
        try:
            text = Path(path).read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = Path(path).read_text(errors="replace")

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return pd.DataFrame()

    for sep in ("\t", ",", ";"):
        parsed = [line.split(sep) for line in lines]
        if len(parsed[0]) > 1 and all(len(row) == len(parsed[0]) for row in parsed):
            return pd.DataFrame(parsed[1:], columns=parsed[0])

    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        return pd.read_csv(path, delim_whitespace=True)


df = read_text_table(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

# The supplied file preview identifies columns by their order and names.
time_col = next((c for c in df.columns if re.search(r"time", c, re.I)), df.columns[0])
temp_col = next((c for c in df.columns if re.search(r"temp", c, re.I)), df.columns[1])
weight_col = next((c for c in df.columns if re.search(r"weight|mass", c, re.I)), df.columns[2])

for col in (time_col, temp_col, weight_col):
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace(",", ".", regex=False).str.extract(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", expand=False),
        errors="coerce",
    )

df = df.dropna(subset=[time_col, temp_col, weight_col]).sort_values(time_col)
time = df[time_col].to_numpy(dtype=float)
weight = df[weight_col].to_numpy(dtype=float)
temperature = df[temp_col].to_numpy(dtype=float)

# Display the measured weight at the sample nearest to 140 minutes.
idx = int(np.argmin(np.abs(time - 140.0)))
label_time = float(time[idx])
label_weight = float(weight[idx])

option = {
    "animation": False,
    "title": {
        "text": "isothermal",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["무게", "온도"],
        "left": "center",
        "top": 38,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    },
    "grid": {"left": 72, "right": 72, "top": 86, "bottom": 62},
    "xAxis": {
        "type": "value",
        "name": "시간 (분)",
        "nameLocation": "middle",
        "nameGap": 38,
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
            "position": "left",
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}},
        },
        {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "position": "right",
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": [
        {
            "name": "무게",
            "type": "line",
            "showSymbol": False,
            "data": [[float(x), float(y)] for x, y in zip(time, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"140분 무게 {label_weight:.2f}%",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [label_time, label_weight]}],
            },
        },
        {
            "name": "온도",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(x), float(y)] for x, y in zip(time, temperature)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
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
