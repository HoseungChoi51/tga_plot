from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B07_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 두 번째 시트(PVC)의 온도와 무게 데이터를 읽습니다.
df = pd.read_excel(DATA_FILE, sheet_name=1)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight)
temperature = temperature[valid]
weight = weight[valid]

# 보간을 위해 온도 순으로 정렬합니다.
order = np.argsort(temperature)
temperature = temperature[order]
weight = weight[order]

targets = [300, 600]
target_weights = [np.interp(t, temperature, weight) for t in targets]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(temperature, weight, color="#2369a1", linewidth=2, label="PVC")
ax.set_title("PVC 열중량 분석")
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("무게 (%)")
ax.set_xlim(temperature.min(), temperature.max())
ax.set_ylim(bottom=0)
ax.grid(True, linestyle="--", alpha=0.35)

colors = ["#d95f02", "#6a3d9a"]
for t, w, color in zip(targets, target_weights, colors):
    ax.axvline(t, color=color, linestyle=":", linewidth=1.5, alpha=0.85)
    ax.scatter([t], [w], color=color, edgecolor="white", linewidth=0.8, s=70, zorder=3)
    ax.annotate(
        f"{t} °C: {w:.2f}%",
        xy=(t, w),
        xytext=(9, 12),
        textcoords="offset points",
        color=color,
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor=color, alpha=0.9),
    )

fig.tight_layout()
fig.savefig(OUT_DIR / "pvc_weight_at_300_600C.png", dpi=300, bbox_inches="tight")
plt.close(fig)
