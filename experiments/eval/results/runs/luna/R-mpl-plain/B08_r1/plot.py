from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B08_r1/out"

# Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the Raw worksheet
df = pd.read_excel(DATA_FILE, sheet_name="Raw")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
valid = temperature.notna() & weight.notna()

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(temperature[valid], weight[valid], color="#2b6f9c", linewidth=1.8)

# 50% weight reference line
ax.axhline(50, color="#d9534f", linewidth=1.2, linestyle="--", label="무게 50%")

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_xlim(temperature[valid].min(), temperature[valid].max())
ax.set_ylim(0, 105)
ax.grid(True, color="#d9d9d9", linewidth=0.7, alpha=0.8)
ax.legend(loc="lower left", frameon=False)

# Experimental-condition note in the upper-right corner
ax.text(
    0.98, 0.97, "공기, 10 °C/min",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=11,
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=3),
)

fig.tight_layout()
out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "raw_weight_50_percent.png", dpi=300, bbox_inches="tight")
plt.close(fig)
