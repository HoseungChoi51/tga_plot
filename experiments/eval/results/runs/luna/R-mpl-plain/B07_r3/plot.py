from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B07_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 두 번째 시트(PVC)의 온도와 무게 데이터를 읽습니다.
df = pd.read_excel(DATA_FILE, sheet_name=1)
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight)
temperature, weight = temperature[valid], weight[valid]

# 보간을 위해 온도순으로 정렬합니다.
order = np.argsort(temperature)
temperature, weight = temperature[order], weight[order]

target_temperatures = np.array([300.0, 600.0])
target_weights = np.interp(target_temperatures, temperature, weight)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(temperature, weight, color="#2878B5", linewidth=2, label="무게")
ax.scatter(
    target_temperatures,
    target_weights,
    color="#D9534F",
    edgecolor="white",
    linewidth=0.8,
    s=75,
    zorder=3,
    label="표시 온도",
)

for temp, wt in zip(target_temperatures, target_weights):
    ax.axvline(temp, color="#D9534F", linestyle="--", linewidth=1, alpha=0.6)
    ax.annotate(
        f"{temp:.0f} °C: {wt:.2f}%",
        xy=(temp, wt),
        xytext=(8, 12),
        textcoords="offset points",
        fontsize=10,
        color="#333333",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#D9534F", alpha=0.9),
    )

ax.set_title("PVC 열중량 분석")
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("무게 (%)")
ax.grid(True, linestyle=":", alpha=0.5)
ax.legend()
fig.tight_layout()

fig.savefig(OUT_DIR / "PVC_weight_at_300_600C.png", dpi=300, bbox_inches="tight")
plt.close(fig)
