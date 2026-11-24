import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"

def read_text(path):
    raw = Path(path).read_bytes()
    for encoding in ("utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "cp1252", "latin1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin1", errors="replace")

def load_numeric_columns(path):
    text = read_text(path)
    rows = []
    for line in text.splitlines():
        vals = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?", line)
        if len(vals) >= 3:
            try:
                rows.append([float(v) for v in vals])
            except ValueError:
                pass
    if not rows:
        raise ValueError("No numeric data rows found in input file")
    width = max(map(len, rows))
    arr = np.full((len(rows), width), np.nan, dtype=float)
    for i, row in enumerate(rows):
        arr[i, :len(row)] = row
    return arr

data = load_numeric_columns(DATA_FILE)
if data.shape[1] < 3:
    raise ValueError("Expected at least three numeric columns")

# Export columns are elapsed time, temperature, mass (%), and derivative.
x = data[:, 1]
y = data[:, 2]
valid = np.isfinite(x) & np.isfinite(y)
x, y = x[valid], y[valid]
if not len(y):
    raise ValueError("No valid temperature/mass values found")

residue = float(y[-1])
residue_text = f"Residue: {residue:.2f}%"

option = {
    "animation": False,
    "textStyle": {"fontFamily": "Noto Sans CJK KR"},
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    },
    "grid": {"left": 78, "right": 32, "top": 42, "bottom": 68},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 38,
        "axisLine": {"show": True},
        "splitLine": {"show": False}
    },
    "yAxis": {
        "type": "value",
        "name": "Mass (%)",
        "nameLocation": "middle",
        "nameGap": 52,
        "min": 0,
        "max": 105,
        "axisLine": {"show": True},
        "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}}
    },
    "series": [{
        "name": "Mass",
        "type": "line",
        "showSymbol": False,
        "lineStyle": {"width": 2, "color": "#276FBF"},
        "data": [[float(a), float(b)] for a, b in zip(x, y)]
    }],
    "graphic": [{
        "type": "text",
        "right": 38,
        "top": 12,
        "style": {
            "text": residue_text,
            "fill": "#333333",
            "font": "bold 15px Noto Sans CJK KR"
        }
    }]
}

print(json.dumps({
    "figures": [{
        "name": "tga_plot",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"]
    }]
}, ensure_ascii=False, allow_nan=False))
