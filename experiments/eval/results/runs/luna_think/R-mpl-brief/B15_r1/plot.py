from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna_think/R-mpl-brief/B15_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

colors = ["#1f4e9c", "#2e8b57", "#8e44ad"]
fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
for idx, (sheet_name, df) in enumerate(sheets.items()):
    # Preview indicates temperature, weight and derivative weight are columns B, C and D.
    x = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()
    weight = pd.to_numeric(df.iloc[:, 2], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df.iloc[:, 3], errors="coerce").to_numpy()

    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        continue

    order = np.argsort(x)
    x, weight, dtg = x[order], weight[order], dtg[order]
    color = colors[idx % len(colors)]

    ax1.plot(x, weight, color=color, linewidth=1.8, label=f"{sheet_name} Weight")
    ax2.plot(x, -dtg, color=color, linestyle="--", linewidth=1.5,
             label=f"{sheet_name} DTG")

    # Residue: measured weight at the point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], marker="o", color=color,
             markersize=5, linestyle="none")
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(5, 7), textcoords="offset points",
        color=color, fontsize=8
    )

    # Peak: highest upward-pointing DTG peak at temperatures above 150 °C.
    eligible = x > 150
    if np.any(eligible):
        eligible_indices = np.flatnonzero(eligible)
        peak_idx = int(eligible_indices[np.argmax(-dtg[eligible])])
        ax2.plot(x[peak_idx], -dtg[peak_idx], marker="^", color=color,
                 markersize=5, linestyle="none")
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], -dtg[peak_idx]),
            xytext=(5, -12), textcoords="offset points",
            color=color, fontsize=8
        )

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (−%/°C)")
ax1.set_title("TGA — PE, PVC, PET")
ax1.grid(True, linestyle=":", alpha=0.5)

handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="center left", bbox_to_anchor=(1.12, 0.5), frameon=True)

fig.tight_layout()
fig.savefig(OUT_DIR / "polymers_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
