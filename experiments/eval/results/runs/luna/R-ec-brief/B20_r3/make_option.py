import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
SHEET = "Acid-washed"


def clean_name(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_").lower() or "plot"


df = pd.read_excel(DATA_FILE, sheet_name=SHEET)
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern):
    matches = [c for c in df.columns if re.search(pattern, c, re.IGNORECASE)]
    if not matches:
        raise ValueError(f"Required column not found: {pattern}")
    return matches[0]

x_col = find_column(r"temperature")
weight_col = find_column(r"weight")
dtg_col = find_column(r"deriv|dtg")

x = pd.to_numeric(df[x_col], errors="coerce").to_numpy(dtype=float)
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy(dtype=float)
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy(dtype=float)

valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
x, weight, dtg = x[valid], weight[valid], dtg[valid]

residue_idx = int(np.argmin(np.abs(x - 800)))
peak_candidates = np.flatnonzero(x > 150)
peak_idx = int(peak_candidates[np.argmin(dtg[peak_candidates])]) if len(peak_candidates) else int(np.argmin(dtg))

xmin, xmax = float(np.min(x)), float(np.max(x))
weight_min, weight_max = float(np.min(weight)), float(np.max(weight))
dtg_positive = -dtg
dtg_min, dtg_max = float(np.min(dtg_positive)), float(np.max(dtg_positive))

weight_pad = max((weight_max - weight_min) * 0.06, 1.0)
dtg_pad = max((dtg_max - dtg_min) * 0.06, 0.05)

option = {
    "title": {
        "text": SHEET,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Weight (%)", "DTG (-)"],
        "left": "center",
        "top": 38,
        "orient": "vertical",
        "textStyle": {"fontFamily": "Noto Sans CJK KR"}
    },
    "grid": {"left": 76, "right": 76, "top": 96, "bottom": 66},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": xmin,
        "max": xmax,
        "minorTick": {"show": True, "splitNumber": 5},
        "minorSplitLine": {"show": False},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
        "axisLine": {"show": True},
        "axisTick": {"show": True}
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": weight_min - weight_pad,
            "max": weight_max + weight_pad,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}}
        },
        {
            "type": "value",
            "name": "DTG (-)",
            "nameLocation": "middle",
            "nameGap": 50,
            "min": dtg_min - dtg_pad,
            "max": dtg_max + dtg_pad,
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
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "itemStyle": {"color": "#1f4e9c"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {weight[residue_idx]:.1f}%",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "data": [{"coord": [float(x[residue_idx]), float(weight[residue_idx])]}]
            }
        },
        {
            "name": "DTG (-)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "data": [[float(a), float(b)] for a, b in zip(x, dtg_positive)],
            "lineStyle": {"color": "#c0392b", "width": 2},
            "itemStyle": {"color": "#c0392b"},
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 8,
                "itemStyle": {"color": "#c0392b"},
                "label": {
                    "show": True,
                    "formatter": f"{x[peak_idx]:.0f} °C",
                    "position": "top",
                    "fontFamily": "Noto Sans CJK KR"
                },
                "data": [{"coord": [float(x[peak_idx]), float(dtg_positive[peak_idx])]}]
            }
        }
    ]
}

result = {
    "figures": [{
        "name": clean_name(SHEET),
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}
print(json.dumps(result, ensure_ascii=False, allow_nan=False))
