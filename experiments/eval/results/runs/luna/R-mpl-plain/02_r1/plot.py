from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/02_r1/out")
OUT_FILE = OUT_DIR / "1006R1-V_normal_TGA.png"
SHEET_NAME = "1006R1-V normal"

# Korean-capable font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

# Select columns by their expected names, with positional fallback for the described B/C/D columns.
def find_column(expected_name, fallback_index):
    for column in df.columns:
        if expected_name.lower() in column.lower():
            return column
    return df.columns[fallback_index]

temperature_col = find_column("Temperature", 1)
weight_col = find_column("Weight", 2)
derivative_col = find_column("D.W", 3)

data = df[[temperature_col, weight_col, derivative_col]].apply(
    pd.to_numeric, errors="coerce"
).dropna()

temperature = data[temperature_col].to_numpy()
weight = data[weight_col].to_numpy()
derivative = data[derivative_col].to_numpy()

# Find the observation closest to 800 °C and the maximum derivative value.
residue_index = int(np.argmin(np.abs(temperature - 800)))
residue_temperature = temperature[residue_index]
residue_weight = weight[residue_index]

max_derivative_index = int(np.argmax(derivative))
max_derivative = derivative[max_derivative_index]
max_derivative_temperature = temperature[max_derivative_index]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(
    temperature, weight, color="#1f77b4", linewidth=2, label="Weight"
)
line2, = ax2.plot(
    temperature, derivative, color="#d62728", linewidth=1.8,
    label="Deriv. Weight"
)

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f77b4")
ax2.set_ylabel("Deriv. Weight (%/°C)", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#d62728")

# Temperature ticks start at 0 and increase by 200 °C.
x_max = float(np.nanmax(temperature))
ax1.set_xlim(left=0, right=x_max)
ax1.set_xticks(np.arange(0, x_max + 1, 200))

# Weight ticks every 20%.
weight_min = min(0.0, float(np.nanmin(weight)))
weight_max = max(100.0, float(np.nanmax(weight)))
ax1.set_ylim(weight_min, weight_max)
ax1.set_yticks(np.arange(0, 101, 20))

# Derivative ticks every 0.2, with limits rounded outward to those increments.
step = 0.2
deriv_min = np.floor(np.nanmin(derivative) / step) * step
deriv_max = np.ceil(np.nanmax(derivative) / step) * step
if deriv_min == deriv_max:
    deriv_max = deriv_min + step
ax2.set_ylim(deriv_min, deriv_max)
ax2.set_yticks(np.arange(deriv_min, deriv_max + step * 0.5, step))

# Mark and label the maximum derivative value.
ax2.scatter(
    [max_derivative_temperature], [max_derivative],
    color="#d62728", edgecolor="white", linewidth=0.8, zorder=5
)
ax2.annotate(
    f"Max = {max_derivative:.4g} %/°C",
    xy=(max_derivative_temperature, max_derivative),
    xytext=(10, 14),
    textcoords="offset points",
    color="#d62728",
    fontsize=9,
    arrowprops={"arrowstyle": "->", "color": "#d62728", "lw": 1},
)

# Identify the weight at the measured temperature nearest 800 °C.
ax1.scatter(
    [residue_temperature], [residue_weight],
    color="#1f77b4", edgecolor="white", linewidth=0.8, zorder=5
)
ax1.annotate(
    f"Residue {residue_weight:.2f}%\n({residue_temperature:.1f} °C)",
    xy=(residue_temperature, residue_weight),
    xytext=(12, -30),
    textcoords="offset points",
    color="#1f77b4",
    fontsize=9,
    arrowprops={"arrowstyle": "->", "color": "#1f77b4", "lw": 1},
)

ax1.set_title("1006R1-V normal — TGA")
ax1.grid(True, which="major", linestyle="--", alpha=0.35)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")
fig.tight_layout()

OUT_DIR.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT_FILE, dpi=300, bbox_inches="tight")
plt.close(fig)
