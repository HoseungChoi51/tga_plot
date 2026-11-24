from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B11_r3/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="PET")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
dtg_up = -dtg
dtg_line, = ax2.plot(temperature, dtg_up, color="#c0392b", label="DTG (%/°C)")

# Residue at the measured point nearest 800 °C
residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue = weight[residue_idx]
ax1.plot(residue_temp, residue, marker="o", color="#1f4e9c", zorder=5)
ax1.annotate(
    f"Residue {residue:.2f}%",
    xy=(residue_temp, residue),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
)

# Highest upward DTG peak above 150 °C
peak_candidates = np.flatnonzero(temperature > 150)
peak_idx = peak_candidates[np.argmax(dtg_up[peak_candidates])]
peak_temp = temperature[peak_idx]
peak_value = dtg_up[peak_idx]
ax2.plot(peak_temp, peak_value, marker="o", color="#c0392b", zorder=5)
ax2.annotate(
    f"{peak_temp:.0f} °C",
    xy=(peak_temp, peak_value),
    xytext=(8, 10),
    textcoords="offset points",
    color="#c0392b",
)

ax1.set_title("PET 열분해")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("-DTG (%/°C)")
ax1.grid(True, alpha=0.35)
ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG (%/°C)"], loc="lower left")

fig.tight_layout()
fig.savefig(Path(OUT_DIR) / "PET_열분해.png", dpi=300, bbox_inches="tight")
plt.close(fig)
