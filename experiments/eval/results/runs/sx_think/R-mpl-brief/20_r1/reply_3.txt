```python
import os
import re
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = os.environ.get("DATA_FILE") or "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = os.environ.get("OUT_DIR") or "/home/chs/Work/tga_plot/eval/results/runs/sx_think/R-mpl-brief/20_r1/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.sans-serif": ["Noto Sans CJK KR", "DejaVu Sans"],
    "axes.unicode_minus": False,
})

EXCEL_EXTS = {".xlsx", ".xls", ".xlsm"}


def parse_file_list(value):
    if not value:
        return []

    value = str(value).strip()

    if value.startswith(("[", "(", "{")):
        try:
            return [str(x) for x in ast.literal_eval(value)]
        except Exception:
            pass

    if ";" in value:
        return [p.strip() for p in value.split(";") if p.strip()]

    if os.pathsep and os.pathsep in value:
        return [p.strip() for p in value.split(os.pathsep) if p.strip()]

    if "\n" in value:
        return [p.strip() for p in value.splitlines() if p.strip()]

    return [value]


def unique_paths(paths):
    seen = set()
    out = []
    for p in paths:
        p = str(p).strip()
        if not p:
            continue
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def collect_data_files():
    paths = parse_file_list(DATA_FILE) + parse_file_list(os.environ.get("DATA_FILES"))
    paths = unique_paths(paths)
    existing = [p for p in paths if Path(p).exists()]

    if not existing and DATA_FILE and Path(DATA_FILE).exists():
        existing = [DATA_FILE]

    return existing


def get_sheets(path):
    ext = Path(path).suffix.lower()
    if ext in EXCEL_EXTS:
        return list(pd.ExcelFile(path).sheet_names)
    return [Path(path).stem]


def read_raw(path, sheet=None):
    ext = Path(path).suffix.lower()
    if ext in EXCEL_EXTS:
        return pd.read_excel(path, sheet_name=sheet, header=None)
    return pd.read_csv(path, header=None)


def find_header_row(raw):
    n = min(20, len(raw))

    for i in range(n):
        row = raw.iloc[i]

        if row.notna().sum() < 2:
            continue

        has_string = False
        for v in row:
            if isinstance(v, str) and v.strip():
                has_string = True
                break

        if not has_string:
            continue

        if i + 1 >= len(raw):
            continue

        nxt = raw.iloc[i + 1]
        numeric_count = 0

        for j in range(len(row)):
            if pd.isna(row[j]) or pd.isna(nxt[j]):
                continue
            try:
                float(nxt[j])
                numeric_count += 1
            except (TypeError, ValueError):
                pass

        if numeric_count >= 2:
            return i

    return -1


def load_sheet(path, sheet):
    raw = read_raw(path, sheet)

    if raw is None or raw.empty:
        return pd.DataFrame()

    h = find_header_row(raw)

    if h < 0:
        df = raw.copy()
        header = [f"col_{j + 1}" for j in range(df.shape[1])]
    else:
        header_row = raw.iloc[h]
        header = []

        for j, val in enumerate(header_row):
            name = "" if pd.isna(val) else str(val).strip()
            if not name:
                name = f"col_{j + 1}"
            header.append(name)

        df = raw.iloc[h + 1:].copy()

    if df.empty:
        return pd.DataFrame()

    df.columns = header

    counts = {}
    cols = []
    for c in df.columns:
        c = str(c)
        if c in counts:
            counts[c] += 1
            cols.append(f"{c}_{counts[c]}")
        else:
            counts[c] = 0
            cols.append(c)

    df.columns = cols

    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(how="all")
    return df.reset_index(drop=True)


def find_tga_columns(df):
    if df.empty or df.shape[1] < 3:
        return None, None, None

    lower = [str(c).lower() for c in df.columns]

    x_idx = None
    y1_idx = None
    y2_idx = None

    for i, name in enumerate(lower):
        if any(k in name for k in ("dtg", "d.w", "d w", "derivative", "dw")):
            y2_idx = i
            break

    for i, name in enumerate(lower):
        if "temp" in name:
            x_idx = i
            break

    for i, name in enumerate(lower):
        if "weight" in name and i != y2_idx:
            y1_idx = i
            break

    numeric_cols = []
    for i in range(df.shape[1]):
        s = df.iloc[:, i].dropna()
        if s.empty:
            continue
        try:
            arr = s.to_numpy(dtype=float)
            arr = arr[np.isfinite(arr)]
            if arr.size > 0:
                numeric_cols.append(i)
        except (TypeError, ValueError):
            pass

    if len(numeric_cols) < 3:
        return None, None, None

    def valid(i):
        return i is not None and i in numeric_cols

    x_idx = x_idx if valid(x_idx) else None
    y1_idx = y1_idx if valid(y1_idx) else None
    y2_idx = y2_idx if valid(y2_idx) else None

    def col_range(i):
        s = df.iloc[:, i].dropna().to_numpy(dtype=float)
        s = s[np.isfinite(s)]
        return float(s.max() - s.min()) if s.size else -np.inf

    def weight_score(i):
        s = df.iloc[:, i].dropna().to_numpy(dtype=float)
        s = s[np.isfinite(s)]
        if s.size == 0:
            return (np.inf, np.inf, np.inf)
        good = 0 if (50 <= s.max() <= 110 and s.min() >= 0) else 1
        return (good, abs(float(s.max()) - 100.0), float(s.min()))

    def derivative_score(i):
        s = df.iloc[:, i].dropna().to_numpy(dtype=float)
        s = s[np.isfinite(s)]
        if s.size == 0:
            return (np.inf, np.inf)
        has_neg = 0 if s.min() < 0 else 1
        return (has_neg, float(s.abs().max()))

    chosen = []

    for pos, idx in enumerate((x_idx, y1_idx, y2_idx)):
        if idx is None or idx in chosen:
            candidates = [i for i in numeric_cols if i not in chosen]
            if not candidates:
                return None, None, None

            if pos == 0:
                idx = max(candidates, key=col_range)
            elif pos == 1:
                idx = min(candidates, key=weight_score)
            else:
                idx = min(candidates, key=derivative_score)

        chosen.append(idx)

    if len(chosen) < 3:
        return None, None, None

    return chosen[0], chosen[1], chosen[2]


def safe_filename(name, fallback):
    s = re.sub(r"[^\w\-]+", "_", str(name), flags=re.UNICODE).strip("._")
    return s or fallback


def plot_tga(df, title, out_path