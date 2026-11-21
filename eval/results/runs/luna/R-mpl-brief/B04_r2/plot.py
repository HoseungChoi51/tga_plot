from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B04_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the CSV and use its first two columns as 2θ and intensity.
df = pd.read_csv(DATA_FILE)
if df.shape[1] < 2:
    raise ValueError("XRD 데이터에는 x(2θ)와 intensity 열이 필요합니다.")

x = pd.to_numeric(df.iloc[:, 0], errors="coerce").to_numpy()
y = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()
valid = np.isfinite(x) & np.isfinite(y)
x, y = x[valid], y[valid]

if len(x) == 0:
    raise ValueError("유효한 XRD 데이터가 없습니다.")

order = np.argsort(x)
x, y = x[order], y[order]

# Find local maxima, then select the five strongest peaks.
peak_indices, _ = find_peaks(y)
if len(peak_indices) == 0:
    peak_indices = np.array([int(np.argmax(y))])

strongest = peak_indices[np.argsort(y[peak_indices])[-5:]]
strongest = strongest[np.argsort(x[strongest])]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(x, y, color="#1f4e9c", linewidth=1.2)
ax.scatter(x[strongest], y[strongest], color="#c0392b", s=32, zorder=3)

y_span = max(float(np.max(y) - np.min(y)), 1.0)
for idx in strongest:
    ax.annotate(
        f"{x[idx]:.2f}°",
        xy=(x[idx], y[idx]),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#8e2b20",
    )

ax.set_title("XRD 패턴")
ax.set_xlabel("2θ (deg)")
ax.set_ylabel("Intensity (counts)")
ax.set_xlim(float(np.min(x)), float(np.max(x)))
ax.set_ylim(bottom=min(0, float(np.min(y)) - 0.02 * y_span))
ax.grid(True, linestyle="--", alpha=0.35)
fig.tight_layout()

fig.savefig(OUT_DIR / "xrd_pattern.png", dpi=300, bbox_inches="tight")
plt.close(fig)
