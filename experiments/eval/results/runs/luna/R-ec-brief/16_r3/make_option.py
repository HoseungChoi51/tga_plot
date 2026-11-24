import json
import os
import re
import sys

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

def clean_name(value):
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text

def main():
    sheets = pd.read_excel(DATA_FILE, sheet_name=None, engine="openpyxl")
    if SHEET_NAME not in sheets:
        raise ValueError(f"시트를 찾을 수 없습니다: {SHEET_NAME}")

    df = sheets[SHEET_NAME].copy()
    df.columns = [clean_name(c) for c in df.columns]

    x_col = next((c for c in df.columns if "temperature" in c.lower()), None)
    y_col = next((c for c in df.columns if "weight" in c.lower()), None)
    if x_col is None or y_col is None:
        raise ValueError("Temperature 또는 Weight 열을 찾을 수 없습니다.")

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(df[y_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if not len(x):
        raise ValueError("그릴 수 있는 숫자 데이터가 없습니다.")

    data = [[round(float(a), 6), round(float(b), 6)] for a, b in zip(x, y)]

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR"},
        "title": {
            "text": SHEET_NAME,
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
        },
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 72, "right": 34, "top": 66, "bottom": 64},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 36,
            "min": float(np.nanmin(x)),
            "max": float(np.nanmax(x)),
            "axisLine": {"show": True, "lineStyle": {"color": "#333333"}},
            "axisTick": {"show": True},
            "axisLabel": {"color": "#333333"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
        },
        "yAxis": {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 52,
            "axisLine": {"show": True, "lineStyle": {"color": "#333333"}},
            "axisTick": {"show": True},
            "axisLabel": {"color": "#333333"},
            "splitLine": {"show": True, "lineStyle": {"color": "#e5e5e5"}}
        },
        "series": [{
            "name": "Weight (%)",
            "type": "line",
            "data": data,
            "showSymbol": False,
            "symbol": "none",
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "yAxisIndex": 0,
            "connectNulls": False,
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": "{b}",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "data": []
            }
        }]
    }

    near_800 = int(np.argmin(np.abs(x - 800.0)))
    residue_x, residue_y = float(x[near_800]), float(y[near_800])
    option["series"][0]["markPoint"]["data"].append({
        "name": f"Residue {residue_y:.1f}%",
        "coord": [residue_x, residue_y]
    })

    payload = {
        "figures": [{
            "name": "1006R1-V_normal",
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"]
        }]
    }
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))

if __name__ == "__main__":
    main()
