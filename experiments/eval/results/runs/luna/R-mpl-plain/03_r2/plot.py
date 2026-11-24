from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/03_r2/out"
SHEET_NAME = "1006R1-V acid"

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(col).strip() for col in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight(%)"], errors="coerce").to_numpy()
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce").to_numpy()

valid = (
    np.isfinite(temperature)
    & np.isfinite(weight)
    & np.isfinite(derivative)
    & (temperature >= 100)
    & (temperature <= 800)
)
temperature = temperature[valid]
weight = weight[valid]
derivative = derivative[valid]

order = np.argsort(temperature)
temperature = temperature[order]
weight = weight[order]
derivative = derivative[order]

# TGA mass-loss peaks are represented by minima in D.W(%/C).
peaks, _ = find_peaks(-derivative, distance=max(1, len(derivative) // 20))
if len(peaks) < 2:
    peaks, _ = find_peaks(-derivative, distance=1)

if len(peaks) >= 2:
    peak_indices = peaks[np.argsort(derivative[peaks])[:2]]
else:
    # Fallback: select the two strongest derivative minima, including endpoints.
    peak_indices = np.argsort(derivative)[:2]

peak_indices = np.sort(peak_indices)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax_weight = plt.subplots(figsize=(9, 5.5))
ax_derivative = ax_weight.twinx()

weight_line, = ax_weight.plot(
    temperature, weight, color="#2457A6", linewidth=2, label="Weight(%)"
)
derivative_line, = ax_derivative.plot(
    temperature, derivative, color="#D1495B", linewidth=1.8, label="D.W(%/C)"
)

for i, idx in enumerate(peak_indices, start=1):
    peak_temp = temperature[idx]
    peak_value = derivative[idx]
    ax_derivative.scatter(
        peak_temp, peak_value, color="#D1495B", edgecolor="white",
        linewidth=0.8, s=65, zorder=5
    )
    ax_derivative.annotate(
        f"피크 {i}: {peak_temp:.1f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, -20 if i == 1 else 12),
        textcoords="offset points",
        fontsize=9,
        color="#9F2636",
        arrowprops=dict(arrowstyle="->", color="#9F2636", lw=0.9),
    )

ax_weight.set_xlim(100, 800)
ax_weight.set_xlabel("온도 (°C)")
ax_weight.set_ylabel("Weight (%)", color="#2457A6")
ax_derivative.set_ylabel("D.W (%/°C)", color="#D1495B")
ax_weight.tick_params(axis="y", labelcolor="#2457A6")
ax_derivative.tick_params(axis="y", labelcolor="#D1495B")
ax_weight.set_title(f"{SHEET_NAME} TGA / DTG")
ax_weight.grid(True, linestyle="--", alpha=0.35)

ax_weight.legend(
    [weight_line, derivative_line],
    [weight_line.get_label(), derivative_line.get_label()],
    loc="best",
    frameon=False,
)

fig.tight_layout()
fig.savefig(out_dir / "1006R1-V_acid_TGA_DTG.png", dpi=300, bbox_inches="tight")
plt.close(fig)
