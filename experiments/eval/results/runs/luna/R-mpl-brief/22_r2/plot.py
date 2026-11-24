from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/22_r2/out"

GREEN = "green"
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

def find_column(columns, keywords):
    for column in columns:
        name = str(column).strip().lower()
        if any(keyword in name for keyword in keywords):
            return column
    return None

def numeric_series(frame, column):
    return pd.to_numeric(frame[column], errors="coerce")

def safe_filename(name):
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(name))

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
for sheet_name, frame in sheets.items():
    x_col = find_column(frame.columns, ("temperature", "temp", "온도"))
    weight_col = find_column(frame.columns, ("weight", "mass", "중량", "무게"))
    dtg_col = find_column(frame.columns, ("d.w", "dtg", "derivative", "미분"))

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    x = numeric_series(frame, x_col)
    weight = numeric_series(frame, weight_col)
    dtg = numeric_series(frame, dtg_col)

    valid = x.notna() & weight.notna() & dtg.notna()
    x = x[valid].to_numpy()
    weight = weight[valid].to_numpy()
    dtg = dtg[valid].to_numpy()
    if not len(x):
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(x, weight, color="#1f4e9c", label="Weight (%)", linewidth=1.8)
    dtg_line, = ax2.plot(x, -dtg, color=GREEN, label="DTG", linewidth=1.8)

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (%/°C)", color=GREEN)
    ax2.tick_params(axis="y", colors=GREEN)
    ax2.spines["right"].set_color(GREEN)

    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], marker="o", color="#1f4e9c")
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax((-dtg)[peak_candidates])]
        ax2.plot(x[peak_idx], -dtg[peak_idx], marker="o", color=GREEN)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], -dtg[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color=GREEN,
        )

    ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG"], loc="center left")
    ax1.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
