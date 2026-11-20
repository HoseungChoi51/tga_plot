import csv
import json
import os
import re

import numpy as np
import pandas as pd

DATA_FILES = [
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv",
    "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt",
]


def load_data(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)

    if ext in (".xls", ".xlsx"):
        return pd.read_excel(path)

    # TGA text exports may be tab-separated, whitespace-separated, or
    # semicolon/comma-delimited, and can include a few metadata lines.
    encodings = ("utf-8-sig", "utf-16", "cp1252", "latin1")
    text = None
    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                text = f.read()
            break
        except (UnicodeError, OSError):
            continue
    if text is None:
        raise ValueError(f"Unable to read text file: {path}")

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"File is empty: {path}")

    # Find the likely header row by looking for the temperature column.
    header_idx = next(
        (i for i, line in enumerate(lines) if re.search(r"temperature", line, re.I)),
        0,
    )
    candidates = lines[header_idx:]

    sample = "\n".join(candidates[:10])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = None

    if delimiter:
        rows = list(csv.reader(candidates, delimiter=delimiter))
        if rows:
            width = max(map(len, rows))
            rows = [row + [""] * (width - len(row)) for row in rows]
            df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
        else:
            df = pd.DataFrame()
    else:
        df = pd.read_csv(
            path,
            sep=r"\s+",
            engine="python",
            skiprows=header_idx,
            encoding=next((e for e in encodings if _can_decode(path, e)), "latin1"),
        )

    # If the first parsing attempt did not produce useful rows, retry using
    # pandas' delimiter inference and skip non-table metadata.
    if df.empty or len(df.columns) < 2:
        df = pd.read_csv(
            path,
            sep=None,
            engine="python",
            skiprows=header_idx,
            encoding=next((e for e in encodings if _can_decode(path, e)), "latin1"),
        )
    return df


def _can_decode(path, encoding):
    try:
        with open(path, "r", encoding=encoding) as f:
            f.read()
        return True
    except (UnicodeError, OSError):
        return False


def normalized_name(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def choose_column(df, patterns, fallback):
    names = list(df.columns)
    for col in names:
        normalized = normalized_name(col)
        if any(re.search(pattern, normalized) for pattern in patterns):
            return col
    if len(names) > fallback:
        return names[fallback]
    raise ValueError(f"Cannot identify required data column from: {names}")


def numeric_column(series):
    # Handle decimal commas and numbers surrounded by units or other text.
    values = series.astype(str).str.strip()
    values = values.str.replace(",", ".", regex=False)
    values = values.str.extract(r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)", expand=False)
    return pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)


datasets = []
for path, label in zip(DATA_FILES, ("Lot A", "Lot B")):
    df = load_data(path)

    # Drop blank/unnamed columns often found in instrument text exports.
    df = df.loc[:, [
        c for c in df.columns
        if not str(c).lower().startswith("unnamed") and str(c).strip()
    ]]
    xcol = choose_column(df, (r"temperature", r"temp"), 1)
    ycol = choose_column(df, (r"weight", r"mass"), 2)
    dcol = choose_column(df, (r"deriv", r"dtg"), 3)

    x = numeric_column(df[xcol])
    weight = numeric_column(df[ycol])
    dtg = numeric_column(df[dcol])
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if not len(x):
        # As a robust fallback, parse numeric records from the text table and
        # use the expected TGA column order: time, temperature, weight, DTG.
        if os.path.splitext(path)[1].lower() not in (".xls", ".xlsx", ".csv"):
            with open(path, "r", encoding="latin1") as f:
                raw_lines = f.read().splitlines()
            records = []
            for line in raw_lines:
                nums = re.findall(
                    r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?",
                    line.replace(",", "."),
                )
                if len(nums) >= 4:
                    try:
                        records.append([float(v) for v in nums[-4:]])
                    except ValueError:
                        pass
            if records:
                arr = np.asarray(records, dtype=float)
                x, weight, dtg = arr[:, 1], arr[:, 2], arr[:, 3]
                valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
                x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if not len(x):
        raise ValueError(f"No numeric TGA rows found in {path}")

    residue_idx = int(np.argmin(np.abs(x - 800)))
    candidates = np.flatnonzero(x > 150)
    peak_idx = int(candidates[np.argmax(-dtg[candidates])]) if len(candidates) else None
    datasets.append({
        "label": label,
        "x": x,
        "weight": weight,
        "dtg": -dtg,
        "residue_idx": residue_idx,
        "peak_idx": peak_idx,
    })


weight_colors = {"Lot A": "#1f4e9c", "Lot B": "#27ae60"}
dtg_colors = {"Lot A": "#c0392b", "Lot B": "#e67e22"}
series = []

for item in datasets:
    label = item["label"]
    color = weight_colors[label]
    dtg_color = dtg_colors[label]

    series.extend([
        {
            "name": label,
            "type": "line",
            "yAxisIndex": 0,
            "showSymbol": False,
            "lineStyle": {"width": 2, "color": color},
            "data": [[float(x), float(y)] for x, y in zip(item["x"], item["weight"])],
        },
        {
            "name": label + " DTG",
            "type": "line",
            "yAxisIndex": 1,
            "showSymbol": False,
            "lineStyle": {"width": 1.8, "color": dtg_color},
            "data": [[float(x), float(y)] for x, y in zip(item["x"], item["dtg"])],
        },
    ])

    ri = item["residue_idx"]
    series.append({
        "name": label + " residue marker",
        "type": "scatter",
        "yAxisIndex": 0,
        "symbolSize": 9,
        "itemStyle": {"color": color, "borderColor": "#ffffff", "borderWidth": 1},
        "data": [{
            "value": [float(item["x"][ri]), float(item["weight"][ri])],
            "label": {
                "show": True,
                "formatter": f'Residue {item["weight"][ri]:.1f}%',
                "position": "top",
                "fontSize": 11,
                "color": color,
            },
        }],
        "tooltip": {"show": False},
    })

    pi = item["peak_idx"]
    if pi is not None:
        series.append({
            "name": label + " peak marker",
            "type": "scatter",
            "yAxisIndex": 1,
            "symbolSize": 9,
            "itemStyle": {"color": dtg_color},
            "data": [{
                "value": [float(item["x"][pi]), float(item["dtg"][pi])],
                "label": {
                    "show": True,
                    "formatter": f'{item["x"][pi]:.0f} °C',
                    "position": "top",
                    "fontSize": 11,
                    "color": dtg_color,
                },
            }],
            "tooltip": {"show": False},
        })

option = {
    "animation": False,
    "title": {
        "text": "TGA Comparison",
        "left": "center",
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 16},
    },
    "tooltip": {"trigger": "axis"},
    "legend": {
        "data": ["Lot A", "Lot B"],
        "left": "center",
        "bottom": 4,
        "textStyle": {"fontFamily": "Noto Sans CJK KR", "fontSize": 11},
    },
    "grid": {"left": 68, "right": 68, "top": 58, "bottom": 66},
    "xAxis": {
        "type": "value",
        "name": "Temperature (°C)",
        "nameLocation": "middle",
        "nameGap": 34,
        "axisLine": {"show": True},
        "axisTick": {"show": True},
        "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
        "splitLine": {"show": False},
    },
    "yAxis": [
        {
            "type": "value",
            "name": "Weight (%)",
            "nameLocation": "middle",
            "nameGap": 48,
            "min": 0,
            "max": 105,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": True, "lineStyle": {"color": "#dddddd"}},
        },
        {
            "type": "value",
            "name": "-DTG (%/°C)",
            "nameLocation": "middle",
            "nameGap": 48,
            "axisLine": {"show": True},
            "axisTick": {"show": True},
            "axisLabel": {"fontFamily": "Noto Sans CJK KR"},
            "splitLine": {"show": False},
        },
    ],
    "series": series,
}

print(json.dumps({
    "figures": [{
        "name": "tga_lot_comparison",
        "option": option,
        "width": 614,
        "height": 442,
        "dpi": 300,
        "formats": ["png"],
    }]
}, ensure_ascii=False, allow_nan=False))
