from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B14_r3/out")

SHEET_NAME = "PVC"
FIGSIZE = (10, 6.5)
FONT_SIZE = 16

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": FONT_SIZE,
    "axes.titlesize": FONT_SIZE,
    "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": FONT_SIZE,
    "ytick.labelsize": FONT_SIZE,
    "legend.fontsize": FONT_SIZE,
    "axes.unicode_minus": False,
})

data = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
data.columns = [str(column).strip() for column in data.columns]

# The workbook preview identifies columns B, C, and D as temperature, weight, and derivative weight.
temperature = pd.to_numeric(data.iloc[:, 1], errors="coerce").to_numpy()
weight = pd.to_numeric(data.iloc[:, 2], errors="coerce").to_numpy()
dtg = pd.to_numeric(data.iloc[:, 3], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature = temperature[valid]
weight = weight[valid]
dtg = dtg[valid]

if temperature.size == 0:
    raise ValueError(f"No valid TGA data found in sheet {SHEET_NAME!r}.")

residue_idx = int(np.argmin(np.abs(temperature - 800)))
peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size == 0:
    raise ValueError("No data points above 150 °C were found.")
peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])

fig, ax1 = plt.subplots(figsize=FIGSIZE)
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=2.2, label="Weight (%)"
)
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=2.0, label="-DTG (%/°C)"
)

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("-DTG (%/°C)")

ax1.plot(
    temperature[residue_idx], weight[residue_idx],
    marker="o", markersize=8, color="#1f4e9c", zorder=5
)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(10, 12), textcoords="offset points",
    color="#1f4e9c", fontsize=FONT_SIZE,
)

ax2.plot(
    temperature[peak_idx], -dtg[peak_idx],
    marker="o", markersize=8, color="#c0392b", zorder=5
)
ax2.annotate(
    f"{temperature[peak_idx]:.0f} °C",
    (temperature[peak_idx], -dtg[peak_idx]),
    xytext=(10, 12), textcoords="offset points",
    color="#c0392b", fontsize=FONT_SIZE,
)

ax1.legend(
    handles=[weight_line, dtg_line],
    loc="center left",
    frameon=True,
)
ax1.grid(True, alpha=0.25)
fig.tight_layout()

output_file = OUT_DIR / "PVC_TGA.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)
