from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/04_r3/out")
SHEET_NAME = "1006R1-V normal"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
dtg = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)", linewidth=1.8)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax1.set_title("CNT 산화 거동", fontsize=18, color="navy")
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(temperature, -dtg, color="#c0392b", label="-DTG (%/°C)", linewidth=1.5)
ax2.set_ylabel("-DTG (%/°C)")

residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_weight = weight[residue_idx]
ax1.scatter([residue_temp], [residue_weight], color="#1f4e9c", zorder=5)
ax1.annotate(
    f"Residue {residue_weight:.1f}%",
    xy=(residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
)

peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size:
    peak_idx = peak_candidates[np.argmax(-dtg[peak_candidates])]
    peak_temp = temperature[peak_idx]
    peak_value = -dtg[peak_idx]
    ax2.scatter([peak_temp], [peak_value], color="#c0392b", zorder=5)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
    )

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V_normal.png", dpi=300, bbox_inches="tight")
plt.close(fig)
