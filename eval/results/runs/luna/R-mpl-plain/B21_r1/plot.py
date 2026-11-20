from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B21_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()
temperature, weight, derivative = (
    temperature[valid],
    weight[valid],
    derivative[valid],
)

fig, ax_weight = plt.subplots(figsize=(9, 6))
ax_derivative = ax_weight.twinx()

line_weight, = ax_weight.plot(
    temperature, weight, color="#1f77b4", linewidth=2, label="Weight (%)"
)
line_derivative, = ax_derivative.plot(
    temperature,
    derivative,
    color="#d62728",
    linewidth=1.6,
    label="Deriv. Weight (%/°C)",
)

ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)", color="#1f77b4")
ax_derivative.set_ylabel("Deriv. Weight (%/°C)", color="#d62728")
ax_weight.tick_params(axis="y", labelcolor="#1f77b4")
ax_derivative.tick_params(axis="y", labelcolor="#d62728")
ax_weight.set_xlim(temperature.max(), temperature.min())
ax_weight.grid(True, linestyle="--", alpha=0.35)
ax_weight.set_title("Raw")
ax_weight.legend(
    [line_weight, line_derivative],
    [line_weight.get_label(), line_derivative.get_label()],
    loc="best",
)
fig.tight_layout()

fig.savefig(OUT_DIR / "raw_tga_reversed_temperature.png", dpi=300, bbox_inches="tight")
plt.close(fig)
