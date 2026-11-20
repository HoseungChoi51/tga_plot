import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
SHEET_NAME = "1006R1-V normal"

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_column(pattern, fallback_index):
    for col in df.columns:
        if re.search(pattern, col, re.IGNORECASE):
            return col
    return df.columns[fallback_index]

x_col = find_column(r"temperature|temp", 1)
weight_col = find_column(r"weight", 2)
dtg_col = find_column(r"d\.?\s*w|deriv", 3)

data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
x = data[x_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

residue_idx = int(np.argmin(np.abs(x - 800)))
residue_x = float(x[residue_idx])
residue_y = float(weight[residue_idx])

# DTG is conventionally negative during mass loss; plot its inverted value.
dtg_plot = -dtg
valid_peak = np.flatnonzero(x > 150)
peak_idx = int(valid_peak[np.argmax(dtg_plot[valid_peak])]) if len(valid_peak) else int(np.argmax(dtg_plot))
peak_x = float(x[peak_idx])
peak_y = float(dtg_plot[peak_idx])

option = {
    "animation": False,
    "title": {
        "text": SHEET_NAME,
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16}
    },
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Weight(%)", "Deriv.Weight"], "left": "center", "bottom": 8},
    "grid": {"left": 76, "right": 76, "top": 62, "bottom": 86},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "min": 0,
        "max": 1000,
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
            "name": "Deriv.Weight",
            "nameLocation": "middle",
            "nameGap": 52,
            "min": 0,
            "max": 1.2,
            "interval": 0.2,
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "nameTextStyle": {"fontFamily": "Noto Sans CJK KR"}
        }
    ],
    "series": [
        {
            "name": "Weight(%)",
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"color": "#1f4e9c", "width": 2},
            "data": [[float(a), float(b)] for a, b in zip(x, weight)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "data": [{
                    "coord": [residue_x, residue_y],
                    "name": "Residue",
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_y:.1f}%",
                        "position": "top",
                        "fontFamily": "Noto Sans CJK KR"
                    }
                }]
            }
        },
        {
            "name": "Deriv.Weight",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"color": "#c0392b", "width": 2},
            "data": [[float(a), float(b)] for a, b in zip(x, dtg_plot)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#c0392b"},
                "data": [{
                    "coord": [peak_x, peak_y],
                    "name": "Max Deriv.Weight",
                    "label": {
                        "show": True,
                        "formatter": f"Max {peak_y:.3g}",
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
        "name": "1006R1-V_normal",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
