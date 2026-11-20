from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B11_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the PET worksheet and normalize the column labels.
df = pd.read_excel(DATA_FILE, sheet_name="PET")
df.columns = [str(column).strip() for column in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col and "Deriv" not in col)
derivative_col = next(col for col in df.columns if "Deriv" in col)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
derivative = pd.to_numeric(df[derivative_col], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()
temperature, weight, derivative = (
    temperature[valid],
    weight[valid],
    derivative[valid],
)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax_weight = plt.subplots(figsize=(9, 6))
ax_derivative = ax_weight.twinx()

line_weight, = ax_weight.plot(
    temperature, weight, color="tab:blue", linewidth=2, label="잔류량"
)
line_derivative, = ax_derivative.plot(
    temperature, derivative, color="tab:red", linewidth=1.8, label="미분 잔류량"
)

ax_weight.set_title("PET 열분해")
ax_weight.set_xlabel("온도 (°C)")
ax_weight.set_ylabel("잔류량 (%)", color="tab:blue")
ax_derivative.set_ylabel("미분 잔류량 (%/°C)", color="tab:red")
ax_weight.tick_params(axis="y", labelcolor="tab:blue")
ax_derivative.tick_params(axis="y", labelcolor="tab:red")

ax_weight.grid(True, which="major", linestyle="--", alpha=0.5)
ax_weight.legend(
    [line_weight, line_derivative],
    ["잔류량", "미분 잔류량"],
    loc="lower left",
)

# Report the final measured residue to two decimal places.
residue = float(weight.iloc[-1])
ax_weight.text(
    0.98,
    0.04,
    f"잔류량: {residue:.2f}%",
    transform=ax_weight.transAxes,
    ha="right",
    va="bottom",
    fontsize=10,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.85},
)

fig.tight_layout()
fig.savefig(OUT_DIR / "PET_열분해.png", dpi=300, bbox_inches="tight")
plt.close(fig)
