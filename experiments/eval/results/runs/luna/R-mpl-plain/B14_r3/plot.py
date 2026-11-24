from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B14_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": 16,
    "axes.titlesize": 20,
    "axes.labelsize": 16,
    "legend.fontsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "axes.linewidth": 1.4,
})

df = pd.read_excel(DATA_FILE, sheet_name="PVC")
df.columns = [str(column).strip() for column in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)
derivative_col = next(c for c in df.columns if "Deriv" in c)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
derivative = pd.to_numeric(df[derivative_col], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()
temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]

fig, ax_weight = plt.subplots(figsize=(10, 6.2), constrained_layout=True)

line_weight, = ax_weight.plot(
    temperature, weight,
    color="#1769AA", linewidth=2.8, label="Weight"
)
ax_weight.set_xlabel("Temperature (°C)", labelpad=10)
ax_weight.set_ylabel("Weight (%)", color="#1769AA", labelpad=10)
ax_weight.tick_params(axis="y", labelcolor="#1769AA")
ax_weight.set_xlim(temperature.min(), temperature.max())
ax_weight.set_ylim(0, 105)
ax_weight.grid(True, color="#D7DDE3", linewidth=0.8, alpha=0.8)
ax_weight.set_title("PVC 열중량 분석 (TGA)", pad=16, weight="bold")

ax_derivative = ax_weight.twinx()
line_derivative, = ax_derivative.plot(
    temperature, derivative,
    color="#D1495B", linewidth=2.4, label="Derivative weight"
)
ax_derivative.set_ylabel("Deriv. Weight (%/°C)", color="#D1495B", labelpad=10)
ax_derivative.tick_params(axis="y", labelcolor="#D1495B")

ax_weight.legend(
    [line_weight, line_derivative],
    ["Weight (%)", "Deriv. Weight (%/°C)"],
    loc="upper right",
    frameon=True,
    framealpha=0.95,
)

fig.savefig(OUT_DIR / "PVC_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
