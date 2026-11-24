import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"


def read_text_table(path):
    raw = Path(path).read_bytes()
    text = None
    for encoding in ("utf-16", "utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("latin-1", errors="replace")

    # Instrument exports may contain metadata before the numeric table.
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        fields = re.split(r"[\t,; ]+", stripped)
        numeric = pd.to_numeric(pd.Series(fields), errors="coerce")
        if numeric.notna().sum() >= 3:
            rows.append(fields)

    if not rows:
        return pd.DataFrame()

    width = max(map(len, rows))
    normalized = [row + [None] * (width - len(row)) for row in rows]
    return pd.DataFrame(normalized).apply(pd.to_numeric, errors="coerce")


def read_data(path):
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(p, sheet_name=None, header=None)
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
            try:
                return {"instrument_export": pd.read_csv(p, header=None, encoding=encoding)}
            except (UnicodeDecodeError, pd.errors.ParserError):
                pass
        return {"instrument_export": read_text_table(p)}
    return {"instrument_export": read_text_table(p)}


def choose_columns(df):
    arr = df.apply(pd.to_numeric, errors="coerce")
    arr = arr.dropna(how="all").dropna(axis=1, how="all")
    if arr.shape[1] < 3:
        return None

    # Common TGA export layout: time, temperature, weight, derivative weight.
    if arr.shape[1] >= 4:
        return (
            arr.iloc[:, 1].to_numpy(dtype=float),
            arr.iloc[:, 2].to_numpy(dtype=float),
            arr.iloc[:, 3].to_numpy(dtype=float),
        )

    return (
        arr.iloc[:, 0].to_numpy(dtype=float),
        arr.iloc[:, 1].to_numpy(dtype=float),
        arr.iloc[:, 2].to_numpy(dtype=float),
    )


def clean_xy(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    return x[mask], y[mask]


def main():
    figures = []

    for sheet_name, raw in read_data(DATA_FILE).items():
        selected = choose_columns(raw)
        if selected is None:
            continue

        x, weight, dtg = selected
        x, weight = clean_xy(x, weight)
        xd, dtg = clean_xy(selected[0], selected[2])
        if len(x) < 2 or len(xd) < 2:
            continue

        residue_idx = int(np.nanargmin(np.abs(x - 800.0)))
        residue_temp = float(x[residue_idx])
        residue = float(weight[residue_idx])

        peak_mask = xd > 150
        peak_temp = None
        peak_y = None
        peak_label = ""
        if np.any(peak_mask):
            peak_indices = np.flatnonzero(peak_mask)
            peak_idx = int(peak_indices[np.nanargmax(-dtg[peak_mask])])
            peak_temp = float(xd[peak_idx])
            peak_y = float(-dtg[peak_idx])
            peak_label = f"{peak_temp:.0f} °C"

        option = {
            "animation": False,
            "title": {
                "text": str(sheet_name),
                "left": "center",
                "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
            },
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Weight", "DTG"], "left": "center", "bottom": 8},
            "grid": {"left": 72, "right": 72, "top": 58, "bottom": 58},
            "xAxis": {
                "type": "value",
                "name": "Temperature (°C)",
                "nameLocation": "middle",
                "nameGap": 32,
                "axisLine": {"show": True},
                "axisTick": {"show": True},
                "splitLine": {"show": False},
            },
            "yAxis": [
                {
                    "type": "value",
                    "name": "Weight (%)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {
                        "show": True,
                        "lineStyle": {"color": "#dddddd"},
                    },
                },
                {
                    "type": "value",
                    "name": "-DTG (%/°C)",
                    "nameLocation": "middle",
                    "nameGap": 48,
                    "axisLine": {"show": True},
                    "axisTick": {"show": True},
                    "splitLine": {"show": False},
                },
            ],
            "series": [
                {
                    "name": "Weight",
                    "type": "line",
                    "showSymbol": False,
                    "data": [[float(a), float(b)] for a, b in zip(x, weight)],
                    "lineStyle": {"color": "#1f4e9c", "width": 2},
                    "itemStyle": {"color": "#1f4e9c"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "data": [
                            {
                                "coord": [residue_temp, residue],
                                "value": residue,
                                "itemStyle": {"color": "#1f4e9c"},
                                "label": {
                                    "show": True,
                                    "formatter": f"Residue: {residue:.1f}%",
                                    "position": "right",
                                    "color": "#1f4e9c",
                                    "fontFamily": "Noto Sans CJK KR",
                                },
                            }
                        ],
                    },
                },
                {
                    "name": "DTG",
                    "type": "line",
                    "yAxisIndex": 1,
                    "showSymbol": False,
                    "data": [[float(a), float(-b)] for a, b in zip(xd, dtg)],
                    "lineStyle": {"color": "#c0392b", "width": 2},
                    "itemStyle": {"color": "#c0392b"},
                    "markPoint": {
                        "symbol": "circle",
                        "symbolSize": 9,
                        "data": (
                            [
                                {
                                    "coord": [peak_temp, peak_y],
                                    "value": peak_y,
                                    "itemStyle": {"color": "#c0392b"},
                                    "label": {
                                        "show": True,
                                        "formatter": peak_label,
                                        "position": "top",
                                        "color": "#c0392b",
                                        "fontFamily": "Noto Sans CJK KR",
                                    },
                                }
                            ]
                            if peak_temp is not None
                            else []
                        ),
                    },
                },
            ],
        }

        name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(sheet_name)).strip("_") or "plot1"
        figures.append(
            {
                "name": name,
                "option": option,
                "width": 614,
                "height": 442,
                "dpi": 300,
                "formats": ["png"],
            }
        )

    print(json.dumps({"figures": figures}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
