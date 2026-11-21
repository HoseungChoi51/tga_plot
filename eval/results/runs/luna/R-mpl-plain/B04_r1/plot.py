from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/xrd.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B04_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and use the first two columns as 2θ and intensity.
df = pd.read_csv(DATA_FILE)
if df.shape[1] < 2:
    raise ValueError("XRD 데이터에는 2θ와 intensity 열이 모두 있어야 합니다.")

x = pd.to_numeric(df.iloc[:, 0], errors="coerce").to_numpy()
y = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()
valid = np.isfinite(x) & np.isfinite(y)
x, y = x[valid], y[valid]

if len(x) == 0:
    raise ValueError("유효한 XRD 데이터가 없습니다.")

order = np.argsort(x)
x, y = x[order], y[order]

# Detect local maxima, then select the five strongest distinct peaks.
peak_indices, _ = find_peaks(y)
if len(peak_indices) == 0:
    peak_indices = np.array([int(np.argmax(y))])

ranked = peak_indices[np.argsort(y[peak_indices])[::-1]]
selected = []
min_separation = max(1, int(round(len(x) * 0.005)))
for idx in ranked:
    if all(abs(idx - prev) >= min_separation for prev in selected):
        selected.append(int(idx))
    if len(selected) == 5:
        break

# If fewer than five distinct local maxima were found, fill from the highest
# remaining intensity values while preserving separation.
if len(selected) < 5:
    for idx in np.argsort(y)[::-1]:
        idx = int(idx)
        if all(abs(idx - prev) >= min_separation for prev in selected):
            selected.append(idx)
        if len(selected) == 5:
            break

selected = sorted(selected, key=lambda idx: x[idx])

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, color="#2457A6", linewidth=1.2)
ax.scatter(x[selected], y[selected], color="#D62728", s=30, zorder=3)

y_range = max(float(np.max(y) - np.min(y)), 1.0)
for i, idx in enumerate(selected):
    offset = 8 + (i % 2) * 12
    ax.annotate(
        f"{x[idx]:.2f}°",
        xy=(x[idx], y[idx]),
        xytext=(0, offset),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#9B1C1C",
        arrowprops=dict(arrowstyle="-", color="#9B1C1C", linewidth=0.7),
    )

ax.set_title("XRD 패턴")
ax.set_xlabel(r"2$\theta$ (deg)")
ax.set_ylabel("Intensity (counts)")
ax.set_xlim(float(np.min(x)), float(np.max(x)))
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.4)
fig.tight_layout()

output_path = OUT_DIR / "xrd_pattern.png"
fig.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close(fig)
