from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B21_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col and "Deriv" not in col)
derivative_col = next(col for col in df.columns if "Deriv" in col)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
derivative = pd.to_numeric(df[derivative_col], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()
temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(temperature, weight, color="#1f77b4", linewidth=2, label="Weight")
line2, = ax2.plot(temperature, derivative, color="#d62728", linewidth=1.8, label="Deriv. Weight")

ax1.set_xlabel(temperature_col)
ax1.set_ylabel(weight_col, color="#1f77b4")
ax2.set_ylabel(derivative_col, color="#d62728")
ax1.tick_params(axis="y", labelcolor="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#d62728")
ax1.set_xlim(temperature.max(), temperature.min())
ax1.grid(True, linestyle="--", alpha=0.35)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")
ax1.set_title("Raw")

fig.tight_layout()
fig.savefig(OUT_DIR / "raw_reversed_temperature.png", dpi=300, bbox_inches="tight")
plt.close(fig)
