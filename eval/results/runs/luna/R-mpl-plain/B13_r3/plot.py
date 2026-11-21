from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B13_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# PVC 시트의 온도와 무게 데이터를 읽고, 결측값 및 비수치값을 제거합니다.
df = pd.read_excel(DATA_FILE, sheet_name="PVC")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
data = pd.DataFrame({"temperature": temperature, "weight": weight}).dropna()
data = data.sort_values("temperature").reset_index(drop=True)

x = data["temperature"].to_numpy()
y = data["weight"].to_numpy()

# 무게 감소 속도(-dW/dT)가 가장 큰 두 구간을 급격한 무게 감소 지점으로 선택합니다.
# 인접한 데이터 점이 같은 꺾임을 중복 표시하지 않도록 최소 간격을 둡니다.
loss_rate = -np.gradient(y, x)
candidates = np.argsort(loss_rate)[::-1]
selected = []
min_separation_c = 30.0

for idx in candidates:
    if loss_rate[idx] <= 0:
        break
    if all(abs(x[idx] - x[chosen]) >= min_separation_c for chosen in selected):
        selected.append(idx)
    if len(selected) == 2:
        break

# 예외적으로 두 지점을 찾지 못한 경우에는 최대 기울기 순으로 보충합니다.
for idx in candidates:
    if len(selected) == 2:
        break
    if idx not in selected:
        selected.append(idx)

selected = sorted(selected, key=lambda i: x[i])

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(x, y, color="#2563a6", linewidth=2.2, label="PVC")
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("무게 (%)")
ax.set_title("PVC의 온도에 따른 무게 변화")
ax.grid(True, linestyle="--", alpha=0.35)

for number, idx in enumerate(selected, start=1):
    temp = x[idx]
    wt = y[idx]
    ax.scatter(temp, wt, color="#d62728", s=55, zorder=4)
    ax.axvline(temp, color="#d62728", linestyle=":", linewidth=1.4, alpha=0.8)
    ax.annotate(
        f"{number}: {temp:.1f} °C",
        xy=(temp, wt),
        xytext=(8, 14 if number == 1 else -24),
        textcoords="offset points",
        color="#a11b1b",
        fontsize=10,
        arrowprops={"arrowstyle": "->", "color": "#a11b1b", "lw": 1},
    )

ax.set_xlim(float(np.min(x)), float(np.max(x)))
ax.set_ylim(bottom=min(0, float(np.min(y)) - 3), top=float(np.max(y)) + 3)
ax.legend(frameon=False, loc="best")
fig.tight_layout()
fig.savefig(OUT_DIR / "PVC_weight_drop_temperatures.png", dpi=300, bbox_inches="tight")
plt.close(fig)
