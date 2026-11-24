from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B13_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean font and readable minus signs
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="PVC")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")

valid = temperature.notna() & weight.notna()
temperature = temperature[valid].to_numpy(dtype=float)
weight = weight[valid].to_numpy(dtype=float)

# Find two prominent mass-loss regions from the negative temperature derivative.
# Smooth the derivative lightly to reduce point-to-point noise, then choose
# separated local minima as the two main drop locations.
order = np.argsort(temperature)
temperature = temperature[order]
weight = weight[order]

derivative = np.gradient(weight, temperature)
window = 11
smoothed = (
    pd.Series(derivative)
    .rolling(window=window, center=True, min_periods=1)
    .mean()
    .to_numpy()
)

candidate_idx = []
for i in range(1, len(smoothed) - 1):
    if smoothed[i] <= smoothed[i - 1] and smoothed[i] < smoothed[i + 1]:
        candidate_idx.append(i)

# Rank local minima by drop steepness; enforce separation so each marked
# temperature corresponds to a distinct mass-loss event.
ranked = sorted(candidate_idx, key=lambda i: smoothed[i])
chosen = []
min_separation = 80.0  # °C
for idx in ranked:
    if all(abs(temperature[idx] - temperature[j]) >= min_separation for j in chosen):
        chosen.append(idx)
    if len(chosen) == 2:
        break

# Fallback: choose the two strongest derivative points with the same separation.
if len(chosen) < 2:
    chosen = []
    for idx in np.argsort(smoothed):
        if all(abs(temperature[idx] - temperature[j]) >= min_separation for j in chosen):
            chosen.append(int(idx))
        if len(chosen) == 2:
            break

chosen = sorted(chosen, key=lambda i: temperature[i])
event_temps = [temperature[i] for i in chosen]

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(temperature, weight, color="#245a8d", linewidth=2, label="PVC 무게")
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("무게 (%)")
ax.set_title("PVC 열중량 분석 — 주요 무게 감소 온도")
ax.set_xlim(float(np.nanmin(temperature)), float(np.nanmax(temperature)))
ax.set_ylim(bottom=0)
ax.grid(True, linestyle=":", alpha=0.45)

for n, (idx, temp) in enumerate(zip(chosen, event_temps), start=1):
    mass = weight[idx]
    ax.axvline(temp, color="#d24a3a", linestyle="--", linewidth=1.4, alpha=0.85)
    ax.scatter([temp], [mass], color="#d24a3a", s=38, zorder=4)
    ax.annotate(
        f"{n}차 감소: {temp:.0f} °C",
        xy=(temp, mass),
        xytext=(8, 18 if n == 1 else -30),
        textcoords="offset points",
        color="#9d2f25",
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="#9d2f25", lw=1),
    )

ax.legend(loc="best", frameon=False)
fig.tight_layout()
fig.savefig(OUT_DIR / "PVC_weight_drop_temperatures.png", dpi=300, bbox_inches="tight")
plt.close(fig)
