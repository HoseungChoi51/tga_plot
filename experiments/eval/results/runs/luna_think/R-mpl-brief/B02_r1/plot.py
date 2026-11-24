from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna_think/R-mpl-brief/B02_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)
df.columns = [str(column).strip() for column in df.columns]

def find_column(fragment):
    matches = [column for column in df.columns if fragment.lower() in column.lower()]
    if not matches:
        raise ValueError(f"필요한 열을 찾을 수 없습니다: {fragment}")
    return matches[0]

temperature_col = find_column("Temperature")
weight_col = find_column("Weight")
heat_flow_col = find_column("Heat Flow")

data = pd.DataFrame({
    "temperature": pd.to_numeric(df[temperature_col], errors="coerce"),
    "weight": pd.to_numeric(df[weight_col], errors="coerce"),
    "heat_flow": pd.to_numeric(df[heat_flow_col], errors="coerce"),
}).dropna().sort_values("temperature")

x = data["temperature"].to_numpy()
weight = data["weight"].to_numpy()
heat_flow = data["heat_flow"].to_numpy()

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
line2, = ax2.plot(x, heat_flow, color="#c0392b", linewidth=1.5, label="Heat Flow (W/g)")

# 잔류량: 측정 온도 중 800 °C에 가장 가까운 지점
residue_idx = int(np.argmin(np.abs(x - 800)))
ax1.scatter(x[residue_idx], weight[residue_idx], color="#1f4e9c", s=36, zorder=5)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (x[residue_idx], weight[residue_idx]),
    xytext=(8, 8),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

# 양의 국소 극대값 중 큰 두 개를 흡열 피크로 표시합니다.
# 음의 국소 극소값 중 가장 낮은 하나를 발열 피크로 표시합니다.
positive_peaks, _ = find_peaks(heat_flow)
negative_peaks, _ = find_peaks(-heat_flow)

positive_peaks = [i for i in positive_peaks if heat_flow[i] > 0]
negative_peaks = [i for i in negative_peaks if heat_flow[i] < 0]

if not positive_peaks and np.max(heat_flow) > 0:
    positive_peaks = [int(np.argmax(heat_flow))]
if not negative_peaks and np.min(heat_flow) < 0:
    negative_peaks = [int(np.argmin(heat_flow))]

endo_indices = sorted(positive_peaks, key=lambda i: heat_flow[i], reverse=True)[:2]
exo_indices = sorted(negative_peaks, key=lambda i: heat_flow[i])[:1]

for rank, idx in enumerate(endo_indices, start=1):
    ax2.scatter(x[idx], heat_flow[idx], color="#c0392b", edgecolor="white", s=48, zorder=6)
    ax2.annotate(
        f"흡열 {rank}: {x[idx]:.0f} °C",
        (x[idx], heat_flow[idx]),
        xytext=(8, 10 + (rank - 1) * 15),
        textcoords="offset points",
        color="#c0392b",
        fontsize=9,
    )

for idx in exo_indices:
    ax2.scatter(x[idx], heat_flow[idx], color="#7d3c98", edgecolor="white", s=48, zorder=6)
    ax2.annotate(
        f"발열: {x[idx]:.0f} °C",
        (x[idx], heat_flow[idx]),
        xytext=(8, -18),
        textcoords="offset points",
        color="#7d3c98",
        fontsize=9,
    )

ax1.set_title(DATA_FILE.stem)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("Heat Flow (W/g)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / f"{DATA_FILE.stem}.png", dpi=300, bbox_inches="tight")
plt.close(fig)
