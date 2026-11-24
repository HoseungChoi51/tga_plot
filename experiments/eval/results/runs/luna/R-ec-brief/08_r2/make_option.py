import json
import re
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"

BLUE = "#1f4e9c"
RED = "#c0392b"
FONT = "Noto Sans CJK KR"


def clean_name(value):
    name = re.sub(r"[^\w가-힣.-]+", "_", str(value).strip())
    return name.strip("_") or "plot"


def find_column(columns, terms):
    for col in columns:
        text = str(col).strip().lower()
        if all(term.lower() in text for term in terms):
            return col
    return None


def make_option(sheet_name, frame):
    frame = frame.dropna(how="all").copy()
    frame.columns = [str(c).strip() for c in frame.columns]

    xcol = find_column(frame.columns, ["temperature"])
    y1col = find_column(frame.columns, ["weight"])
    y2col = find_column(frame.columns, ["d.w"]) or find_column(frame.columns, ["dtg"])

    if xcol is None or y1col is None or y2col is None:
        numeric_cols = [c for c in frame.columns if pd.to_numeric(frame[c], errors="coerce").notna().any()]
        if len(numeric_cols) < 3:
            return None
        xcol, y1col, y2col = numeric_cols[-3:]

    x = pd.to_numeric(frame[xcol], errors="coerce")
    y1 = pd.to_numeric(frame[y1col], errors="coerce")
    y2 = pd.to_numeric(frame[y2col], errors="coerce")
    data = pd.DataFrame({"x": x, "y1": y1, "y2": y2}).dropna().sort_values("x")
    if data.empty:
        return None

    xs = data["x"].to_numpy(dtype=float)
    weights = data["y1"].to_numpy(dtype=float)
    dtg_up = -data["y2"].to_numpy(dtype=float)

    residue_idx = int(np.argmin(np.abs(xs - 800.0)))
    residue_x = float(xs[residue_idx])
    residue_y = float(weights[residue_idx])

    peak_candidates = np.flatnonzero(xs > 150.0)
    peak_idx = int(peak_candidates[np.argmax(dtg_up[peak_candidates])]) if len(peak_candidates) else int(np.argmax(dtg_up))
    peak_x = float(xs[peak_idx])
    peak_y = float(dtg_up[peak_idx])

    return {
        "animation": False,
        "backgroundColor": "#ffffff",
        "textStyle": {"fontFamily": FONT, "color": "#333333"},
        "title": {
            "text": str(sheet_name),
            "left": "center",
            "top": 8,
            "textStyle": {"fontFamily": FONT, "fontSize": 16, "fontWeight": "normal"},
        },
        "legend": {
            "data": ["무게", "미분 무게"],
            "left": 18,
            "top": "middle",
            "orient": "vertical",
            "textStyle": {"fontFamily": FONT, "fontSize": 11},
        },
        "grid": {"left": 90, "right": 82, "top": 60, "bottom": 72},
        "tooltip": {"trigger": "axis"},
        "xAxis": {
            "type": "value",
            "name": "온도 (°C)",
            "nameLocation": "middle",
            "nameGap": 38,
            "axisLine": {"show": True, "lineStyle": {"color": "#555555"}},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": FONT, "fontSize": 10},
            "nameTextStyle": {"fontFamily": FONT, "fontSize": 12},
            "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "무게 (%)",
                "nameLocation": "middle",
                "nameGap": 52,
                "axisLine": {"show": True, "lineStyle": {"color": BLUE}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": FONT, "fontSize": 10, "color": BLUE},
                "nameTextStyle": {"fontFamily": FONT, "fontSize": 12, "color": BLUE},
                "splitLine": {"show": True, "lineStyle": {"color": "#e6e6e6"}},
            },
            {
                "type": "value",
                "name": "미분 무게 (%/°C)",
                "nameLocation": "middle",
                "nameGap": 58,
                "axisLine": {"show": True, "lineStyle": {"color": RED}},
                "axisTick": {"show": True},
                "axisLabel": {"fontFamily": FONT, "fontSize": 10, "color": RED},
                "nameTextStyle": {"fontFamily": FONT, "fontSize": 12, "color": RED},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "무게",
                "type": "line",
                "yAxisIndex": 0,
                "showSymbol": False,
                "data": [[float(a), float(b)] for a, b in zip(xs, weights)],
                "lineStyle": {"color": BLUE, "width": 2},
                "itemStyle": {"color": BLUE},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": BLUE},
                    "label": {
                        "show": True,
                        "formatter": f"Residue {residue_y:.1f}%",
                        "position": "right",
                        "fontFamily": FONT,
                        "fontSize": 11,
                        "color": BLUE,
                    },
                    "data": [{"coord": [residue_x, residue_y]}],
                },
            },
            {
                "name": "미분 무게",
                "type": "line",
                "yAxisIndex": 1,
                "showSymbol": False,
                "data": [[float(a), float(b)] for a, b in zip(xs, dtg_up)],
                "lineStyle": {"color": RED, "width": 2},
                "itemStyle": {"color": RED},
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 8,
                    "itemStyle": {"color": RED},
                    "label": {
                        "show": True,
                        "formatter": f"{peak_x:.0f} °C",
                        "position": "top",
                        "fontFamily": FONT,
                        "fontSize": 11,
                        "color": RED,
                    },
                    "data": [{"coord": [peak_x, peak_y]}],
                },
            },
        ],
    }


figures = []
sheets = pd.read_excel(DATA_FILE, sheet_name=None)
for sheet_name, frame in sheets.items():
    option = make_option(sheet_name, frame)
    if option is not None:
        figures.append({
            "name": clean_name(sheet_name),
            "option": option,
            "width": 614,
            "height": 442,
            "dpi": 300,
            "formats": ["png"],
        })

print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))
