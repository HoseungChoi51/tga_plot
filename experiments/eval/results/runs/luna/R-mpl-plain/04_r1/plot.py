from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/04_r1/out"

# Korean font 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 데이터 불러오기
data = pd.read_excel(DATA_FILE, sheet_name="1006R1-V normal")
temperature = pd.to_numeric(data["Temperature"], errors="coerce")
weight = pd.to_numeric(data["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(data["D.W(%/C)"], errors="coerce")

# 결측값 제거
valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid]
weight = weight[valid]
derivative = derivative[valid]

# TGA 및 미분 곡선 그리기
fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature, weight, color="tab:blue", linewidth=2, label="Weight(%)")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.set_xlim(temperature.min(), temperature.max())
ax1.grid(True, linestyle="--", alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(
    temperature,
    derivative,
    color="tab:red",
    linewidth=1.8,
    label="D.W(%/°C)",
)
ax2.set_ylabel("D.W (%/°C)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

ax1.set_title("CNT 산화 거동", fontsize=18, color="navy", pad=12)

lines = ax1.get_lines() + ax2.get_lines()
ax1.legend(lines, [line.get_label() for line in lines], loc="best", frameon=False)

fig.tight_layout()

output_dir = Path(OUT_DIR)
output_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(output_dir / "CNT_산화_거동.png", dpi=300, bbox_inches="tight")
plt.close(fig)
