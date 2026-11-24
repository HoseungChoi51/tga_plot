import json
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"

# Detect common encodings used by Excel-exported Korean CSV files.
df = None
for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-16", "latin1"):
    try:
        df = pd.read_csv(DATA_FILE, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue

if df is None:
    raise RuntimeError(f"Could not decode CSV file: {DATA_FILE}")

df.columns = [str(c).strip() for c in df.columns]

def find_column(required_terms):
    for column in df.columns:
        if all(term in column for term in required_terms):
            return column
    raise KeyError(f"Could not find a column matching {required_terms}; columns: {list(df.columns)}")

temperature_col = find_column(["온도"])
weight_col = find_column(["무게", "%"])
dtg_col = find_column(["미분무게"])

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy(dtype=float)
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

if temperature.size == 0:
    raise ValueError("The CSV contains no valid temperature, weight, and DTG rows.")

residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = float(temperature[residue_idx])
residue_weight = float(weight[residue_idx])

peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size:
    peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
else:
    peak_idx = int(np.argmax(-dtg))
peak_temp = float(temperature[peak_idx])
peak_value = float(-dtg[peak_idx])

option = {
    "animation": False,
    "title": {
        "text": "korean_excel",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["무게(%)", "DTG (-미분무게)"],
        "left": 70,
        "top": "middle",
        "orient": "vertical",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {"left": 85, "right": 85, "top": 70, "bottom": 70},
    "xAxis": {
        "type": "value",
        "name": "온도 (°C)",
        "nameLocation": "middle",
        "nameGap": 42,
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "무게 (%)",
            "nameLocation": "middle",
            "nameGap": 58,
            "min": 0,
            "max": 105,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 58,
            "min": 0,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "무게(%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "data": [[float(x), float(y)] for x, y in zip(temperature, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "data": [{
                    "coord": [residue_temp, residue_weight],
                    "name": "잔류량",
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_weight:.1f}%",
                        "position": "right",
                        "fontFamily": "Noto Sans CJK KR"
                    }
                }]
            }
        },
        {
            "name": "DTG (-미분무게)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(x), float(-y)] for x, y in zip(temperature, dtg)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "data": [{
                    "coord": [peak_temp, peak_value],
                    "name": "DTG peak",
                    "label": {
                        "show": True,
                        "formatter": f"{peak_temp:.0f} °C",
                        "position": "top",
                        "fontFamily": "Noto Sans CJK KR"
                    }
                }]
            }
        }
    ]
}

print(json.dumps({
    "figures": [{
        "name": "korean_excel",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["pdf", "png"]
    }]
}, ensure_ascii=False, allow_nan=False))
