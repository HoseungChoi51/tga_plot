from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B23_r2/out"

SHEET_COLORS = {
    "Raw": "black",
    "Acid-washed": "blue",
    "Annealed": "red",
}

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

for sheet_name, df in sheets.items():
    if not {"Temperature (°C)", "Weight (%)", "Deriv. Weight (%/°C)"}.issubset(df.columns):
        continue

    color = SHEET_COLORS.get(sheet_name, "gray")
    temp = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
    dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")
    valid = temp.notna() & weight.notna() & dtg.notna()
    temp, weight, dtg = temp[valid], weight[valid], dtg[valid]

    ax1.plot(temp, weight, color=color, linewidth=1.8, label=sheet_name)
    ax2.plot(temp, -dtg, color=color, linewidth=1.5, linestyle="--", alpha=0.8)

    residue_idx = (temp - 800).abs().idxmin()
    ax1.plot(temp.loc[residue_idx], weight.loc[residue_idx], marker="o",
             color=color, markersize=5)
    ax1.annotate(
        f"Residue {weight.loc[residue_idx]:.1f}%",
        (temp.loc[residue_idx], weight.loc[residue_idx]),
        xytext=(6, 7), textcoords="offset points", color=color, fontsize=8,
    )

    peak_candidates = dtg[temp > 150]
    if not peak_candidates.empty:
        peak_idx = peak_candidates.idxmin()
        ax2.plot(temp.loc[peak_idx], -dtg.loc[peak_idx], marker="^",
                 color=color, markersize=6)
        ax2.annotate(
            f"{temp.loc[peak_idx]:.0f} °C",
            (temp.loc[peak_idx], -dtg.loc[peak_idx]),
            xytext=(6, 6), textcoords="offset points", color=color, fontsize=8,
        )

ax1.set_title("세 시료 TGA 비교")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend(loc="center left", frameon=True)
fig.tight_layout()
fig.savefig(out_dir / "cnt_batches_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
