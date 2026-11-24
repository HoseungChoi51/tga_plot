import json
import os
import sys

import numpy as np
import pandas as pd


DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
SHEET_NAME = "Raw"
REFERENCE_TEMP = 150.0

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

temp_col = next((c for c in df.columns if "temperature" in c.lower()), None)
weight_col = next((c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower()), None)

if temp_col is None or weight_col is None:
    raise ValueError("Raw 시트에서 Temperature 및 Weight 열을 찾을 수 없습니다.")

temp = pd.to_numeric(df[temp_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temp.notna() & weight.notna()
temp = temp[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)

if temp.size == 0:
    raise ValueError("유효한 온도/무게 데이터가 없습니다.")

# 150 °C에서의 무게를 보간해 기준 무게로 사용합니다.
order = np.argsort(temp)
reference_weight = float(np.interp(REFERENCE_TEMP, temp[order], weight[order]))
if not np.isfinite(reference_weight) or reference_weight == 0:
    raise ValueError("150 °C 기준 무게가 유효하지 않습니다.")

normalized_weight = weight / reference_weight * 100.0
data = [
    [round(float(x), 6), round(float(y), 6)]
    for x, y in zip(temp, normalized_weight)
]

option = {
    "animation": False,
    "backgroundColor": "#ffffff",
    "title": {
        "text": "Raw — 150 °C 건조 기준 무게",
        "left": "center",
        "top": 14,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 18, "fontWeight": "normal"},
    },
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "line"},
        "valueFormatter": "{value}",
    },
    "grid": {"left": 78, "right": 30, "top": 72, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 30,
        "max": 900,
        "axisLine": {"lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e7e7e7"}},
    },
    "yAxis": {
        "type": "value",
        "name": "무게 (150 °C 기준, %)",
        "nameLocation": "middle",
        "nameGap": 56,
        "axisLine": {"show": True, "lineStyle": {"color": "#555"}},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": True, "lineStyle": {"color": "#e7e7e7"}},
    },
    "series": [
        {
            "name": "건조 기준 무게",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"width": 2, "color": "#2468a2"},
            "itemStyle": {"color": "#2468a2"},
            "markLine": {
                "silent": True,
                "symbol": ["none", "none"],
                "lineStyle": {"color": "#888", "type": "dashed", "width": 1},
                "label": {"show": False},
                "data": [{"yAxis": 100}],
            },
        }
    ],
}

result = {
    "figures": [
        {
            "name": "raw_dry_basis_150C",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        }
    ]
}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
