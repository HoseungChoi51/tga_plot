from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/03_r1/out")
SHEET_NAME = "1006R1-V acid"

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight(%)"], errors="coerce").to_numpy()
dtg = pd.to_numeric(df["D.W(%/C)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
order = np.argsort(temperature)
temperature, weight, dtg = temperature[order], weight[order], dtg[order]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
ax2.plot(temperature, -dtg, color="#c0392b", linewidth=1.5, label="-DTG (%/°C)")

# Residue at the measured point nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800)))
ax1.scatter(temperature[residue_idx], weight[residue_idx], color="#1f4e9c",
            edgecolor="white", linewidth=0.8, zorder=5)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10), textcoords="offset points", color="#1f4e9c",
    fontsize=9
)

# Mark the two strongest upward DTG peaks above 150 °C.
eligible = temperature > 150
eligible_indices = np.flatnonzero(eligible)
peak_positions, _ = find_peaks(-dtg[eligible])
candidate_indices = eligible_indices[peak_positions]

if candidate_indices.size < 2:
    candidate_indices = eligible_indices

top_peak_indices = candidate_indices[
    np.argsort((-dtg[candidate_indices]))[-2:]
]
top_peak_indices = top_peak_indices[np.argsort(temperature[top_peak_indices])]

for idx in top_peak_indices:
    peak_temp = temperature[idx]
    ax2.scatter(peak_temp, -dtg[idx], color="#c0392b", edgecolor="white",
                linewidth=0.8, zorder=6)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        (peak_temp, -dtg[idx]),
        xytext=(7, 8), textcoords="offset points", color="#c0392b",
        fontsize=9
    )

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax1.set_xlim(100, 800)
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V_acid.png", dpi=300, bbox_inches="tight")
plt.close(fig)
