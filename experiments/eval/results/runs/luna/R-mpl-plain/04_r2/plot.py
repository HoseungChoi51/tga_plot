from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/04_r2/out")
SHEET_NAME = "1006R1-V normal"

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

data = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
data.columns = [str(column).strip() for column in data.columns]

temperature = pd.to_numeric(data["Temperature"], errors="coerce")
weight = pd.to_numeric(data["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(data["D.W(%/C)"], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()

fig, ax_weight = plt.subplots(figsize=(9, 6))
ax_derivative = ax_weight.twinx()

weight_line, = ax_weight.plot(
    temperature[valid],
    weight[valid],
    color="tab:blue",
    linewidth=2,
    label="Weight(%)",
)
derivative_line, = ax_derivative.plot(
    temperature[valid],
    derivative[valid],
    color="tab:red",
    linewidth=1.8,
    label="D.W(%/C)",
)

ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)", color="tab:blue")
ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
ax_weight.tick_params(axis="y", labelcolor="tab:blue")
ax_derivative.tick_params(axis="y", labelcolor="tab:red")
ax_weight.set_title("CNT 산화 거동", fontsize=18, color="navy", pad=12)
ax_weight.grid(True, linestyle="--", alpha=0.35)
ax_weight.legend(
    [weight_line, derivative_line],
    [weight_line.get_label(), derivative_line.get_label()],
    loc="best",
    frameon=False,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "CNT_산화_거동.png", dpi=300, bbox_inches="tight")
plt.close(fig)
