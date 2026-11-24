from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/06_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)


def numeric_column(df, candidates):
    """Return the first column matching a candidate name, case-insensitively."""
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    for col in df.columns:
        name = str(col).strip().lower()
        if any(candidate.lower() in name for candidate in candidates):
            return col
    return None


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    x_col = numeric_column(df, ["Temperature", "Temp"])
    weight_col = numeric_column(df, ["Weight(%)", "Weight"])
    dtg_col = numeric_column(df, ["D.W(%/C)", "DTG", "Derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    x = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg_up = -data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight")
    ax2.plot(x, dtg_up, color="#c0392b", linewidth=1.6, label="DTG")

    # Residue at the measured point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], "o", color="#1f4e9c", markersize=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        xy=(x[residue_idx], weight[residue_idx]),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward-pointing DTG peak above 150 °C.
    eligible = np.flatnonzero(x > 150)
    if eligible.size:
        peak_idx = int(eligible[np.argmax(dtg_up[eligible])])
        ax2.plot(x[peak_idx], dtg_up[peak_idx], "o", color="#c0392b", markersize=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            xy=(x[peak_idx], dtg_up[peak_idx]),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    # Grid on; legend intentionally omitted.
    ax1.grid(True, which="major", linestyle="--", linewidth=0.6, alpha=0.6)
    fig.tight_layout()

    output_name = str(sheet_name).replace("/", "_").replace("\\", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
