from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B23_r1/out"

SHEETS = ["Raw", "Acid-washed", "Annealed"]
COLORS = {
    "Raw": "black",
    "Acid-washed": "blue",
    "Annealed": "red",
}

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

for sheet in SHEETS:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    df.columns = [str(col).strip() for col in df.columns]

    temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
    dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")
    valid = temperature.notna() & weight.notna() & dtg.notna()
    temperature = temperature[valid].to_numpy()
    weight = weight[valid].to_numpy()
    dtg = dtg[valid].to_numpy()

    color = COLORS[sheet]
    ax1.plot(temperature, weight, color=color, linewidth=1.8, label=f"{sheet} Weight")
    ax2.plot(temperature, -dtg, color=color, linewidth=1.5, linestyle="--", label=f"{sheet} DTG")

    residue_idx = int(np.argmin(np.abs(temperature - 800)))
    ax1.scatter(temperature[residue_idx], weight[residue_idx], color=color, s=30, zorder=5)
    ax1.annotate(
        f"{sheet} Residue {weight[residue_idx]:.1f}%",
        (temperature[residue_idx], weight[residue_idx]),
        xytext=(6, 5),
        textcoords="offset points",
        color=color,
        fontsize=8,
    )

    peak_candidates = np.flatnonzero(temperature > 150)
    if peak_candidates.size:
        peak_idx = peak_candidates[np.argmax((-dtg)[peak_candidates])]
        ax2.scatter(temperature[peak_idx], (-dtg)[peak_idx], color=color, marker="^", s=35, zorder=5)
        ax2.annotate(
            f"{sheet} {temperature[peak_idx]:.0f} °C",
            (temperature[peak_idx], (-dtg)[peak_idx]),
            xytext=(5, 5),
            textcoords="offset points",
            color=color,
            fontsize=8,
        )

ax1.set_title("TGA Comparison")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (-%/°C)")
ax1.grid(True, alpha=0.25)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left", bbox_to_anchor=(0.02, 0.5), fontsize=8)

fig.tight_layout()
fig.savefig(out_dir / "tga_comparison.png", dpi=300, bbox_inches="tight")
plt.close(fig)
