from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B04_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and use its first two columns as 2θ and intensity.
df = pd.read_csv(DATA_FILE)
x = pd.to_numeric(df.iloc[:, 0], errors="coerce").to_numpy()
y = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()
valid = np.isfinite(x) & np.isfinite(y)
x, y = x[valid], y[valid]

if len(x) == 0:
    raise ValueError("The input file contains no valid numeric x-y data.")

order = np.argsort(x)
x, y = x[order], y[order]

# Find local maxima, then select the five with the greatest intensity.
peaks, _ = find_peaks(y)
if len(peaks) == 0:
    peaks = np.array([int(np.argmax(y))])
strongest = peaks[np.argsort(y[peaks])[-5:]]
strongest = strongest[np.argsort(x[strongest])]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, color="#1f4e9c", linewidth=1.2)

ax.set_title("XRD 패턴")
ax.set_xlabel("2Theta (deg)")
ax.set_ylabel("Intensity (counts)")
ax.grid(True, alpha=0.25)

# Label each selected peak with its 2θ value.
y_range = max(float(np.nanmax(y) - np.nanmin(y)), 1.0)
for i, idx in enumerate(strongest):
    ax.scatter(x[idx], y[idx], color="#c0392b", s=28, zorder=3)
    offset = 10 + (i % 2) * 16
    ax.annotate(
        f"{x[idx]:.2f}°",
        xy=(x[idx], y[idx]),
        xytext=(0, offset),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333",
        arrowprops=dict(arrowstyle="-", color="#777777", lw=0.7),
        clip_on=False,
    )

ax.margins(x=0.02, y=0.16)
fig.tight_layout()
fig.savefig(OUT_DIR / "xrd_pattern.png", dpi=300, bbox_inches="tight")
plt.close(fig)
