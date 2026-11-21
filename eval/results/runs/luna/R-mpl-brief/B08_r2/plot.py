from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B08_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheet_name = "Raw"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Select the TGA columns by their names.
temperature_col = next(c for c in df.columns if "Temperature" in str(c))
weight_col = next(c for c in df.columns if "Weight (%)" in str(c))
dtg_col = next(c for c in df.columns if "Deriv" in str(c))

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=2, label="Weight (%)"
)
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=1.8, label="DTG (%/°C)"
)

ax1.set_title(sheet_name)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)

# Horizontal reference line at 50% weight.
ax1.axhline(50, color="0.35", linestyle="--", linewidth=1.2, label="50% weight")

# Residue at the measured point nearest 800 °C.
residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_value = weight[residue_idx]
ax1.plot(residue_temp, residue_value, "o", color="#1f4e9c", markersize=5)
ax1.annotate(
    f"Residue {residue_value:.1f}%",
    xy=(residue_temp, residue_value),
    xytext=(8, 8),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

# Highest DTG peak above 150 °C (DTG is negative during mass loss).
peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size:
    peak_idx = peak_candidates[np.argmax(-dtg[peak_candidates])]
    peak_temp = temperature[peak_idx]
    peak_value = -dtg[peak_idx]
    ax2.plot(peak_temp, peak_value, "o", color="#c0392b", markersize=5)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, 8),
        textcoords="offset points",
        color="#c0392b",
        fontsize=9,
    )

# User-requested note in the upper-right corner.
ax1.text(
    0.98, 0.97, "공기, 10 °C/min",
    transform=ax1.transAxes,
    ha="right", va="top",
    fontsize=11,
)

handles = [weight_line, dtg_line]
labels = [line.get_label() for line in handles]
ax1.legend(handles, labels, loc="center left", frameon=True)

fig.tight_layout()
fig.savefig(OUT_DIR / "Raw.png", dpi=300, bbox_inches="tight")
plt.close(fig)
