import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path(os.environ.get(
    "DATA_FILE",
    "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
))
OUT_DIR = Path(os.environ.get(
    "OUT_DIR",
    "/home/chs/Work/tga_plot/eval/results/runs/sx_think/R-mpl-brief/B11_r1/out"
))

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def read_table(path: Path, sheet_name=None):
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        if sheet_name is None:
            return pd.read_excel(path, sheet_name=0)
        try:
            return pd.read_excel(path, sheet_name=sheet_name)
        except ValueError:
            return pd.read_excel(path, sheet_name=0)
    return pd.read_csv(path)


def find_column(df, terms, exclude_terms=None):
    terms = [t.lower() for t in terms]
    exclude_terms = [t.lower() for t in (exclude_terms or [])]

    for col in df.columns:
        name = str(col).lower()
        if any(term in name for term in terms):
            if exclude_terms and any(term in name for term in exclude_terms):
                continue
            return col
    return None


def main():
    sheet_name = "PET"
    title = "PET 열분해"

    df = read_table(DATA_FILE, sheet_name)
    df.columns = [str(c).strip() for c in df.columns]

    x_col = find_column(df, ["temp", "temperature"])
    y1_col = find_column(
        df,
        ["weight", "wt", "tg"],
        exclude_terms=["deriv", "dtg", "derivative"]
    )
    y2_col = find_column(df, ["deriv", "dtg", "derivative"])

    cols = list(df.columns)
    if x_col is None:
        x_col = cols[1] if len(cols) > 1 else cols[0]
    if y1_col is None:
        y1_col = cols[2] if len(cols) > 2 else cols[-1]
    if y2_col is None:
        y2_col = cols[3] if len(cols) > 3 else cols[-1]

    work = df[[x_col, y1_col, y2_col]].copy()
    for col in work.columns:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    work = work.dropna().sort_values(by=x_col)

    if work.empty:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        ax.set_title(title)
        fig.savefig(OUT_DIR / "PET.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
        return

    temp = work[x_col].to_numpy(dtype=float)
    weight = work[y1_col].to_numpy(dtype=float)
    dtg = work[y2_col].to_numpy(dtype=float)
    dtg_plot = -dtg

    fig, ax1 = plt.subplots(figsize=(8, 6), dpi=300)

    line1, = ax1.plot(
        temp,
        weight,
        color="#1f4e9c",
        linewidth=1.8,
        label="Weight (%)"
    )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax1.set_title(title)
    ax1.grid(True, linestyle="--", alpha=0.45)
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")

    ax2 = ax1.twinx()

    line2, = ax2.plot(
        temp,
        dtg_plot,
        color="#c0392b",
        linewidth=1.8,
        label="DTG (%/°C)"
    )

    ax2.set_ylabel("DTG (%/°C)")
    ax2.grid(False)
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    residue_idx = int(np.argmin(np.abs(temp - 800.0)))
    residue_temp = temp[residue_idx]
    residue_weight = weight[residue_idx]

    ax1.plot(
        residue_temp,
        residue_weight,
        "o",
        color="#1f4e9c",
        markersize=5,
        zorder=5
    )
    ax1.annotate(
        f"Residue {residue_weight:.2f}%",
        xy=(residue_temp, residue_weight),
        xytext=(12, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9
    )

    peak_mask = temp >= 150.0
    if np.any(peak_mask):
        peak_indices = np.where(peak_mask)[0]
        peak_idx = peak_indices[int(np.argmax(dtg_plot[peak_indices]))]
    else:
        peak_idx = int(np.argmax(dtg_plot))

    peak_temp = temp[peak_idx]
    peak_value = dtg_plot[peak_idx]

    ax2.plot(
        peak_temp,
        peak_value,
        "o",
        color="#c0392b",
        markersize=5,
        zorder=5
    )
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(12, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=9
    )

    handles = [line1, line2]
    labels = [line1.get_label(), line2.get_label()]
    ax1.legend(handles, labels, loc="lower left", framealpha=0.9)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "PET.png"
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
