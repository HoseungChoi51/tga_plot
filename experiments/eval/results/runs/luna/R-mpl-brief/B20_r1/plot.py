from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B20_r1/out"
SHEET_NAME = "Acid-washed"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(col).strip() for col in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
dtg = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

if len(temperature) == 0:
    raise ValueError(f"{SHEET_NAME!r} 시트에 유효한 측정값이 없습니다.")

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)"
)
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=1.5, label="-DTG (%/°C)"
)

# Residue: measured weight nearest 800 °C
residue_idx = int(np.argmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_weight = weight[residue_idx]
ax1.plot(residue_temp, residue_weight, "o", color="#1f4e9c", markersize=6)
ax1.annotate(
    f"Residue {residue_weight:.1f}%",
    (residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=10,
)

# Highest upward DTG peak above 150 °C
peak_candidates = np.flatnonzero(temperature > 150)
if len(peak_candidates):
    peak_idx = int(peak_candidates[np.argmax((-dtg)[peak_candidates])])
    peak_temp = temperature[peak_idx]
    peak_value = -dtg[peak_idx]
    ax2.plot(peak_temp, peak_value, "o", color="#c0392b", markersize=6)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        (peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=10,
    )

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# Add minor ticks to the x-axis.
ax1.xaxis.set_minor_locator(AutoMinorLocator())
ax1.tick_params(axis="x", which="minor", length=3)
ax1.tick_params(axis="x", which="major", length=6)

ax1.grid(True, which="major", axis="both", alpha=0.25)
ax1.legend([weight_line, dtg_line], [weight_line.get_label(), dtg_line.get_label()],
           loc="center left")

fig.tight_layout()
fig.savefig(out_dir / "Acid-washed.png", dpi=300, bbox_inches="tight")
plt.close(fig)
