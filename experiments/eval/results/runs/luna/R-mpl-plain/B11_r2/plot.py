from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B11_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="PET")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid]
weight = weight[valid]
derivative = derivative[valid]

# 잔류량은 마지막 측정 지점의 Weight(%)로 계산합니다.
residue = weight.iloc[-1]

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(temperature, weight, color="tab:blue", linewidth=2, label="중량")
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("중량 (%)", color="tab:blue")
ax.tick_params(axis="y", labelcolor="tab:blue")
ax.set_title("PET 열분해")

ax2 = ax.twinx()
ax2.plot(
    temperature,
    derivative,
    color="tab:red",
    linewidth=1.7,
    label="미분 중량",
)
ax2.set_ylabel("미분 중량 (%/°C)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

lines = ax.get_lines() + ax2.get_lines()
labels = [line.get_label() for line in lines]
ax.legend(lines, labels, loc="lower left", frameon=True)

ax.text(
    0.98,
    0.04,
    f"잔류량: {residue:.2f}%",
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "alpha": 0.85},
)

ax.grid(True, which="major", linestyle="--", linewidth=0.7, alpha=0.6)
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.grid(True, which="minor", linestyle=":", linewidth=0.45, alpha=0.35)

fig.tight_layout()
fig.savefig(OUT_DIR / "PET_열분해.png", dpi=300, bbox_inches="tight")
plt.close(fig)
