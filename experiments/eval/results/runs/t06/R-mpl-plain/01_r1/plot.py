import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/t06/R-mpl-plain/01_r1/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": [
        "Noto Sans CJK KR",
        "Noto Sans KR",
        "Malgun Gothic",
        "DejaVu Sans",
    ],
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
})


def find_header_row(raw):
    max_check = min(10, len(raw))
    for i in range(max_check):
        row = raw.iloc[i].astype(str).str.lower().str.strip()
        text = " ".join(row.tolist())
        if ("temperature" in text or "temp" in text) and ("weight" in text or "wt" in text):
            return i
    return 0


def make_unique_columns(values):
    cols = []
    counts = {}
    for v in values:
        c = str(v).strip()
        if c.lower() in {"nan", "none", ""}:
            c = "Unnamed"

        base = c
        if base in counts:
            counts[base] += 1
            c = f"{base}_{counts[base]}"
        else:
            counts[base] = 0

        cols.append(c)
    return cols


def read_sheet(sheet_name):
    raw = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=None)

    if raw.empty:
        return None

    header_row = find_header_row(raw)
    columns = make_unique_columns(raw.iloc[header_row].tolist())

    df = raw.iloc[header_row + 1:].copy()
    if df.empty:
        return None

    df.columns = columns
    df = df.reset_index(drop=True)
    return df


def find_col(df, keywords, exclude=()):
    for col in df.columns:
        lc = str(col).lower()
        if any(e in lc for e in exclude):
            continue
        for kw in keywords:
            if kw in lc:
                return col
    return None


def prepare_sheet(df):
    temp_col = find_col(df, ["temperature", "temp"], exclude=["time"])
    weight_col = find_col(
        df,
        ["weight (%)", "weight(%)", "weight", "wt"],
        exclude=["d.w", "dtg", "derivative", "rate"],
    )
    dtg_col = find_col(df, ["d.w", "dtg", "dw", "derivative", "rate"])

    if temp_col is None or weight_col is None:
        numeric_cols = []
        for col in df.columns:
            conv = pd.to_numeric(df[col], errors="coerce")
            if conv.notna().sum() >= max(5, int(len(df) * 0.5)):
                numeric_cols.append(col)

        if len(numeric_cols) >= 3:
            if temp_col is None:
                temp_col = numeric_cols[1]
            if weight_col is None:
                weight_col = numeric_cols[2]
            if dtg_col is None and len(numeric_cols) >= 4:
                dtg_col = numeric_cols[3]

    if temp_col is None or weight_col is None:
        return None

    if dtg_col is not None and dtg_col == weight_col:
        dtg_col = None

    cols = [temp_col, weight_col]
    if dtg_col is not None:
        cols.append(dtg_col)

    plot_df = df[cols].copy()

    for c in cols:
        plot_df[c] = pd.to_numeric(plot_df[c], errors="coerce")

    plot_df = plot_df.dropna(subset=[temp_col, weight_col])

    if plot_df.empty:
        return None

    if dtg_col is not None and dtg_col in plot_df.columns:
        if plot_df[dtg_col].dropna().empty:
            dtg_col = None
            plot_df = plot_df[[temp_col, weight_col]]

    plot_df = plot_df.sort_values(temp_col).reset_index(drop=True)

    return plot_df, temp_col, weight_col, dtg_col


def safe_filename(name):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", str(name)).strip("_")
    return s if s else "sheet"


def main():
    xl = pd.ExcelFile(DATA_FILE)
    sheet_names = xl.sheet_names

    samples = []

    for idx, sheet_name in enumerate(sheet_names, start=1):
        df = read_sheet(sheet_name)
        if df is None:
            continue

        prepared = prepare_sheet(df)
        if prepared is None:
            continue

        samples.append((idx, sheet_name, prepared))

    if not samples:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No plottable TGA data found", ha="center", va="center")
        ax.axis("off")
        fig.savefig(Path(OUT_DIR) / "tga_empty.png", dpi=300)
        plt.close(fig)
        return

    x_min = min(p[0][p[1]].min() for _, _, p in samples)
    x_max = max(p[0][p[1]].max() for _, _, p in samples)

    weight_min = min(p[0][p[2]].min() for _, _, p in samples)
    weight_max = max(p[0][p[2]].max() for _, _, p in samples)

    dtg_values = [
        v
        for _, _, p in samples
        if p[3] is not None
        for v in p[0][p[3]].dropna()
    ]

    fig, (ax_weight, ax_dtg) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True, dpi=100
    )

    for i, (_, sheet_name, (plot_df, temp_col, weight_col, dtg_col)) in enumerate(samples):
        color = plt.cm.tab10(i % 10)

        ax_weight.plot(
            plot_df[temp_col],
            plot_df[weight_col],
            color=color,
            linewidth=1.5,
            label=sheet_name,
        )

        if dtg_col is not None:
            ax_dtg.plot(
                plot_df[temp_col],
                plot_df[dtg_col],
                color=color,
                linewidth=1.5,
                label=sheet_name,
            )

    ax_weight.set_title("TGA 결과 (Weight & DTG)")
    ax_weight.set_ylabel("Weight (%)")
    ax_weight.set_xlim(x_min, x_max)
    ax_weight.set_ylim(min(0, weight_min - 5), max(100, weight_max + 5))
    ax_weight.grid(True, linestyle=":", alpha=0.6)
    ax_weight.legend(loc="best", fontsize=9)

    ax_dtg.set_xlabel("Temperature (C)")
    ax_dtg.set_ylabel("DTG (%/C)")
    ax_dtg.set_xlim(x_min, x_max)
    ax_dtg.grid(True, linestyle=":", alpha=0.6)

    if dtg_values:
        d_min = min(dtg_values)
        d_max = max(dtg_values)
        pad = max(abs(d_min), abs(d_max), 0.1) * 0.12
        ax_dtg.set_ylim(d_min - pad, d_max + pad)
        ax_dtg.legend(loc="best", fontsize=9)

    fig.tight_layout()
    fig.savefig(Path(OUT_DIR) / "tga_combined.png", dpi=300)
    plt.close(fig)

    for i, (_, sheet_name, (plot_df, temp_col, weight_col, dtg_col)) in enumerate(samples):
        fig, ax1 = plt.subplots(figsize=(8, 6), dpi=100)

        color1 = plt.cm.tab10(i % 10)

        ax1.plot(
            plot_df[temp_col],
            plot_df[weight_col],
            color=color1,
            linewidth=1.5,
            label="Weight (%)",
        )

        ax1.set_title(f"TGA: {sheet_name}")
        ax1.set_xlabel("Temperature (C)")
        ax1.set_ylabel("Weight (%)")
        ax1.set_xlim(plot_df[temp_col].min(), plot_df[temp_col].max())
        ax1.set_ylim(
            min(0, plot_df[weight_col].min() - 5),
            max(100, plot_df[weight_col].max() + 5),
        )
        ax1.grid(True, linestyle=":", alpha=0.6)

        if dtg_col is not None:
            ax2 = ax1.twinx()

            ax2.plot(
                plot_df[temp_col],
                plot_df[dtg_col],
                color="C1",
                linestyle="--",
                linewidth=1.5,
                label="DTG (%/C)",
            )

            d_min = plot_df[dtg_col].min()
            d_max = plot_df[dtg_col].max()
            pad = max(abs(d_min), abs(d_max), 0.1) * 0.12

            ax2.set_ylabel("DTG (%/C)")
            ax2.set_ylim(d_min - pad, d_max + pad)

            lines = ax1.get_lines() + ax2.get_lines()
            labels = [line.get_label() for line in lines]
            ax1.legend(lines, labels, loc="best", fontsize=9)
        else:
            ax1.legend(loc="best", fontsize=9)

        fig.tight_layout()

        out_path = Path(OUT_DIR) / f"tga_{i + 1:02d}_{safe_filename(sheet_name)}.png"
        fig.savefig(out_path, dpi=300)
        plt.close(fig)


if __name__ == "__main__":
    main()
