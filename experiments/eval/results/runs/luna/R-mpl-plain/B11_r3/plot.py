from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B11_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 한글 표시 설정
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="PET")
df.columns = [str(col).strip() for col in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")

valid = temperature.notna() & weight.notna() & derivative.notna()
temperature = temperature[valid]
weight = weight[valid]
derivative = derivative[valid]

residue = weight.iloc[-1]

fig, ax_weight = plt.subplots(figsize=(9, 6))
ax_derivative = ax_weight.twinx()

weight_line, = ax_weight.plot(
    temperature, weight, color="tab:blue", linewidth=2, label="무게"
)
derivative_line, = ax_derivative.plot(
    temperature, derivative, color="tab:red", linewidth=1.8, label="미분 무게"
)

ax_weight.set_title("PET 열분해")
ax_weight.set_xlabel("온도 (°C)")
ax_weight.set_ylabel("무게 (%)", color="tab:blue")
ax_derivative.set_ylabel("미분 무게 (%/°C)", color="tab:red")
ax_weight.tick_params(axis="y", labelcolor="tab:blue")
ax_derivative.tick_params(axis="y", labelcolor="tab:red")

ax_weight.grid(True, linestyle="--", alpha=0.5)
ax_weight.legend(
    [weight_line, derivative_line],
    ["무게", "미분 무게"],
    loc="lower left",
)

ax_weight.text(
    0.98,
    0.04,
    f"잔류량: {residue:.2f}%",
    transform=ax_weight.transAxes,
    ha="right",
    va="bottom",
    bbox={"facecolor": "white", "edgecolor": "0.7", "alpha": 0.9},
)

fig.tight_layout()
fig.savefig(OUT_DIR / "PET_열분해.png", dpi=300, bbox_inches="tight")
plt.close(fig)
