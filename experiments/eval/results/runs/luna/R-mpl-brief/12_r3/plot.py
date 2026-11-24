from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/12_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def find_column(columns, keywords):
    for col in columns:
        name = str(col).strip().lower()
        if any(keyword in name for keyword in keywords):
            return col
    return None


def safe_filename(name):
    return "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(name)).strip()


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    x_col = find_column(df.columns, ["temperature", "temp"])
    weight_col = find_column(df.columns, ["weight", "mass"])
    dtg_col = find_column(df.columns, ["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if len(numeric_cols) < 3:
            continue
        x_col, weight_col, dtg_col = numeric_cols[1:4]

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]
    dtg_up = -dtg

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    line1, = ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    line2, = ax2.plot(x, dtg_up, color="#c0392b", linewidth=1.5, label="-DTG (%/°C)")

    # Residue at the measured point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.scatter(x[residue_idx], weight[residue_idx], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(7, 8),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward-pointing DTG peak above 150 °C.
    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax(dtg_up[peak_candidates])]
        ax2.scatter(x[peak_idx], dtg_up[peak_idx], color="#c0392b", zorder=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], dtg_up[peak_idx]),
            xytext=(7, 8),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    # Vertical reference line and label for oxidation onset.
    ax1.axvline(450, color="gray", linestyle="--", linewidth=1.2)
    ax1.annotate(
        "산화 시작",
        xy=(450, 0.98),
        xycoords=("data", "axes fraction"),
        xytext=(5, -5),
        textcoords="offset points",
        rotation=90,
        va="top",
        ha="left",
        color="dimgray",
        fontsize=10,
    )

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.25)
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")

    fig.tight_layout()
    output_path = OUT_DIR / f"{safe_filename(sheet_name)}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
