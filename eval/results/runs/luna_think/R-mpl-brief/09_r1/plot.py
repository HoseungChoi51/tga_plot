from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna_think/R-mpl-brief/09_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_column(columns, keyword, fallback_index):
    """Find a column by a case-insensitive keyword, or use its expected position."""
    for column in columns:
        if keyword in str(column).strip().lower():
            return column
    return columns[fallback_index]


def safe_filename(name):
    cleaned = "".join(c if c.isalnum() or c in "-_ " else "_" for c in str(name))
    return cleaned.strip().replace(" ", "_") or "sheet"


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    if df.empty or len(df.columns) < 3:
        continue

    x_col = find_column(df.columns, "temperature", 1)
    weight_col = find_column(df.columns, "weight", 2)
    dtg_col = find_column(df.columns, "d.w", 3 if len(df.columns) > 3 else len(df.columns) - 1)

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    data = pd.DataFrame({"x": x, "weight": weight, "dtg": dtg}).dropna()
    if data.empty:
        continue

    data = data.sort_values("x")
    x = data["x"].to_numpy()
    weight = data["weight"].to_numpy()
    dtg = data["dtg"].to_numpy()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(x, -dtg, color="#c0392b", linewidth=1.5, label="DTG")

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (-dW/dT)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    # Tick marks point outward; tick-label font size is 9 on all axes.
    ax1.tick_params(axis="both", direction="out", labelsize=9)
    ax2.tick_params(axis="y", direction="out", labelsize=9)

    # Residue: measured weight at the point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    residue_x = x[residue_idx]
    residue_weight = weight[residue_idx]
    ax1.scatter(
        residue_x, residue_weight, color="#1f4e9c", s=32, zorder=5,
        edgecolor="white", linewidth=0.6
    )
    ax1.annotate(
        f"Residue {residue_weight:.1f}%",
        xy=(residue_x, residue_weight),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # DTG peak: highest upward peak above 150 °C.
    eligible = np.flatnonzero(x > 150)
    if eligible.size:
        peak_idx = eligible[np.argmax(-dtg[eligible])]
        peak_x = x[peak_idx]
        peak_y = -dtg[peak_idx]
        ax2.scatter(
            peak_x, peak_y, color="#c0392b", s=32, zorder=5,
            edgecolor="white", linewidth=0.6
        )
        ax2.annotate(
            f"{peak_x:.0f} °C",
            xy=(peak_x, peak_y),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
