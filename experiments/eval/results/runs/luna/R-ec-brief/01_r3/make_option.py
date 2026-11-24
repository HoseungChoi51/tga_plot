import json
import os
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

def clean_name(value):
    name = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", str(value)).strip("_")
    return name or "plot"

def read_sheets(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        book = pd.ExcelFile(path)
        return [(sheet, pd.read_excel(path, sheet_name=sheet)) for sheet in book.sheet_names]
    if ext == ".csv":
        return [(os.path.splitext(os.path.basename(path))[0], pd.read_csv(path))]
    return [(os.path.splitext(os.path.basename(path))[0], pd.read_csv(path, sep=None, engine="python"))]

figures = []
used_names = set()

for sheet_name, df in read_sheets(DATA_FILE):
    df = df.dropna(how="all")
    normalized = {str(c).strip().lower(): c for c in df.columns}

    def find_col(candidates, fallback):
        for candidate in candidates:
            for key, original in normalized.items():
                if candidate in key:
                    return original
        return df.columns[fallback] if len(df.columns) > fallback else None

    x_col = find_col(["temperature", "temp"], 1)
    weight_col = find_col(["weight", "mass"], 2)
    dtg_col = find_col(["d.w", "dtg", "derivative"], 3)

    if x_col is None or weight_col is None:
        continue

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid = x.notna() & weight.notna()
    x = x[valid].to_numpy(dtype=float)
    weight = weight[valid].to_numpy(dtype=float)

    if dtg_col is not None:
        dtg_series = pd.to_numeric(df.loc[valid, dtg_col], errors="coerce")
        dtg = dtg_series.to_numpy(dtype=float)
    else:
        dtg = np.full(len(x), np.nan)

    good = np.isfinite(x) & np.isfinite(weight)
    x, weight, dtg = x[good], weight[good], dtg[good]
    if len(x) == 0:
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]

    residue_idx = int(np.argmin(np.abs(x - 800.0)))
    residue_x, residue_y = float(x[residue_idx]), float(weight[residue_idx])

    peak_candidates = np.where((x > 150.0) & np.isfinite(dtg))[0]
    peak_idx = None
    if len(peak_candidates):
        peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
        peak_x = float(x[peak_idx])
        peak_y = float(-dtg[peak_idx])

    safe_name = clean_name(sheet_name)
    base_name = safe_name
    suffix = 2
    while safe_name in used_names:
        safe_name = f"{base_name}_{suffix}"
        suffix += 1
    used_names.add(safe_name)

    series = [
        {
            "name": str(weight_col),
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#1f4e9c"},
            "data": [[float(a), float(b)] for a, b in zip(x, weight) if np.isfinite(b)],
            "markPoint": {
                "symbol": "circle",
                "symbolSize": 9,
                "itemStyle": {"color": "#1f4e9c"},
                "label": {
                    "show": True,
                    "formatter": f"Residue {residue_y:.1f}%",
                    "position": "top",
                    "color": "#1f4e9c",
                    "fontFamily": "Noto Sans CJK KR",
                },
                "data": [{"coord": [residue_x, residue_y]}],
            },
        },
        {
            "name": "DTG (-)",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "connectNulls": False,
            "lineStyle": {"width": 2, "color": "#c0392b"},
            "data": [[float(a), float(-b)] for a, b in zip(x, dtg) if np.isfinite(b)],
        },
    ]

    if peak_idx is not None:
        series[1]["markPoint"] = {
            "symbol": "circle",
            "symbolSize": 9,
            "itemStyle": {"color": "#c0392b"},
            "label": {
                "show": True,
                "formatter": f"{peak_x:.0f} °C",
                "position": "top",
                "color": "#c0392b",
                "fontFamily": "Noto Sans CJK KR",
            },
            "data": [{"coord": [peak_x, peak_y]}],
        }

    option = {
        "animation": False,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "color": "#333"},
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
        },
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [str(weight_col), "DTG (-)"], "left": "center", "top": 32},
        "grid": {"left": 72, "right": 72, "top": 82, "bottom": 62},
        "xAxis": {
            "type": "value",
            "name": "Temperature (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "min": float(np.nanmin(x)),
            "max": float(np.nanmax(x)),
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "splitLine": {"show": False},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Weight (%)",
                "nameLocation": "middle",
                "nameGap": 50,
                "min": 0,
                "max": 105,
                "axisLine": {"show": True, "lineStyle": {"color": "#1f4e9c"}},
                "axisTick": {"show": True},
                "axisLabel": {"color": "#1f4e9c"},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "-DTG (%/°C)",
                "nameLocation": "middle",
                "nameGap": 50,
                "axisLine": {"show": True, "lineStyle": {"color": "#c0392b"}},
                "axisTick": {"show": True},
                "axisLabel": {"color": "#c0392b"},
                "splitLine": {"show": False},
            },
        ],
        "series": series,
    }

    figures.append({
        "name": safe_name,
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
