from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B14_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 발표용 글꼴과 기본 스타일
plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": 16,
    "axes.labelsize": 16,
    "axes.titlesize": 19,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "axes.linewidth": 1.4,
    "lines.linewidth": 2.6,
})

data = pd.read_excel(DATA_FILE, sheet_name="PVC")
data.columns = [str(column).strip() for column in data.columns]

temperature_col = next(
    column for column in data.columns
    if "temperature" in column.lower() or "온도" in column
)
weight_col = next(
    column for column in data.columns
    if "weight (%)" in column.lower() and "deriv" not in column.lower()
)
derivative_col = next(
    column for column in data.columns
    if "deriv" in column.lower()
)

temperature = pd.to_numeric(data[temperature_col], errors="coerce")
weight = pd.to_numeric(data[weight_col], errors="coerce")
derivative = pd.to_numeric(data[derivative_col], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()

temperature = temperature[valid]
weight = weight[valid]
derivative = derivative[valid]

fig, ax_weight = plt.subplots(figsize=(10, 6.2), constrained_layout=True)

weight_line, = ax_weight.plot(
    temperature, weight, color="#2166ac", label="Weight"
)
ax_weight.set_xlabel("Temperature (°C)", labelpad=10)
ax_weight.set_ylabel("Weight (%)", color="#2166ac", labelpad=10)
ax_weight.tick_params(axis="y", labelcolor="#2166ac")
ax_weight.set_xlim(temperature.min(), temperature.max())
ax_weight.set_ylim(0, 105)
ax_weight.grid(True, color="#d9d9d9", linewidth=0.8, alpha=0.8)
ax_weight.set_axisbelow(True)

ax_derivative = ax_weight.twinx()
derivative_line, = ax_derivative.plot(
    temperature, derivative, color="#d6604d", label="Derivative weight"
)
ax_derivative.set_ylabel("Derivative weight (%/°C)", color="#d6604d", labelpad=10)
ax_derivative.tick_params(axis="y", labelcolor="#d6604d")

ax_weight.set_title("PVC 열중량 분석 (TGA)", pad=16, weight="bold")
ax_weight.legend(
    [weight_line, derivative_line],
    ["Weight (%)", "Derivative weight (%/°C)"],
    loc="best",
    frameon=True,
    framealpha=0.95,
)

fig.savefig(OUT_DIR / "PVC_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
