from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B13_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load the requested PVC sheet and identify columns by their names.
df = pd.read_excel(DATA_FILE, sheet_name="PVC")
temp_col = next(c for c in df.columns if "temperature" in str(c).lower())
weight_col = next(c for c in df.columns if "weight" in str(c).lower() and "deriv" not in str(c).lower())
dtg_col = next(c for c in df.columns if "deriv" in str(c).lower())

data = df[[temp_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
temperature = data[temp_col].to_numpy()
weight = data[weight_col].to_numpy()
dtg = data[dtg_col].to_numpy()

# Sharp weight drops correspond to the strongest negative DTG peaks.
# Pick the two largest distinct DTG peaks above 150 °C.
candidate_idx, _ = find_peaks(
    -dtg,
    distance=max(1, len(dtg) // 30),
    prominence=max(float(np.nanmax(-dtg)) * 0.04, 1e-9),
)
candidate_idx = candidate_idx[temperature[candidate_idx] > 150]

if len(candidate_idx) >= 2:
    selected = candidate_idx[np.argsort(-dtg[candidate_idx])[:2]]
else:
    # Fallback: select the two most negative DTG samples above 150 °C,
    # separated enough to avoid marking adjacent samples from one event.
    eligible = np.flatnonzero(temperature > 150)
    selected = []
    for idx in eligible[np.argsort(dtg[eligible])]:
        if all(abs(temperature[idx] - temperature[j]) > 25 for j in selected):
            selected.append(int(idx))
        if len(selected) == 2:
            break
    selected = np.asarray(selected, dtype=int)

selected = selected[np.argsort(temperature[selected])]

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.set_title("PVC")
ax1.grid(True, alpha=0.25)

ax2 = ax1.twinx()
ax2.plot(temperature, -dtg, color="#c0392b", linewidth=1.5, label="-DTG")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

# Mark the two sharp mass-loss temperatures directly on the weight curve.
for n, idx in enumerate(selected, start=1):
    t = temperature[idx]
    w = weight[idx]
    ax1.scatter(t, w, color="#1f4e9c", edgecolor="white", linewidth=0.8, s=55, zorder=5)
    ax1.annotate(
        f"{t:.0f} °C",
        xy=(t, w),
        xytext=(10, 15 if n == 1 else -24),
        textcoords="offset points",
        fontsize=10,
        color="#222222",
        arrowprops=dict(arrowstyle="-", color="#555555", linewidth=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
    )

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / "PVC_sharp_weight_drops.png", dpi=300, bbox_inches="tight")
plt.close(fig)
