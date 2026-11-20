from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/02_r2/out"
SHEET_NAME = "1006R1-V normal"

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

# Read the requested sheet and select Temperature, Weight, and Deriv.Weight.
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "temperature" in c.lower())
weight_col = next(c for c in df.columns if "weight" in c.lower() and "deriv" not in c.lower())
derivative_col = next(
    c for c in df.columns
    if "d.w" in c.lower() or "deriv" in c.lower()
)

data = df[[temperature_col, weight_col, derivative_col]].apply(
    pd.to_numeric, errors="coerce"
).dropna()

temperature = data[temperature_col].to_numpy()
weight = data[weight_col].to_numpy()
derivative = data[derivative_col].to_numpy()

# Mark the measured point whose temperature is closest to 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800.0)))
residue_temperature = temperature[residue_idx]
residue_weight = weight[residue_idx]

# Maximum Deriv.Weight value and its corresponding temperature.
derivative_max_idx = int(np.argmax(derivative))
derivative_max = derivative[derivative_max_idx]
derivative_max_temperature = temperature[derivative_max_idx]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(
    temperature, weight, color="tab:blue", linewidth=2, label="Weight (%)"
)
line2, = ax2.plot(
    temperature, derivative, color="tab:red", linewidth=1.8,
    label="Deriv.Weight (%/°C)"
)

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="tab:blue")
ax2.set_ylabel("Deriv.Weight (%/°C)", color="tab:red")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax2.tick_params(axis="y", labelcolor="tab:red")

# Requested tick intervals; temperature ticks begin at 0 °C.
ax1.set_xlim(left=0)
ax1.xaxis.set_major_locator(MultipleLocator(200))
ax1.yaxis.set_major_locator(MultipleLocator(20))
ax2.yaxis.set_major_locator(MultipleLocator(0.2))

# Annotate the maximum derivative value.
ax2.scatter(
    derivative_max_temperature, derivative_max,
    color="darkred", edgecolor="white", linewidth=0.8, zorder=5
)
ax2.annotate(
    f"Max Deriv.Weight: {derivative_max:.3f}\n"
    f"({derivative_max_temperature:.1f} °C)",
    xy=(derivative_max_temperature, derivative_max),
    xytext=(10, 12),
    textcoords="offset points",
    color="darkred",
    fontsize=9,
    arrowprops=dict(arrowstyle="->", color="darkred", lw=0.9),
)

# Annotate residue using the measured temperature closest to 800 °C.
ax1.scatter(
    residue_temperature, residue_weight,
    color="navy", edgecolor="white", linewidth=0.8, zorder=5
)
ax1.annotate(
    f"Residue {residue_weight:.2f}%\n"
    f"({residue_temperature:.1f} °C; closest to 800 °C)",
    xy=(residue_temperature, residue_weight),
    xytext=(12, -30),
    textcoords="offset points",
    color="navy",
    fontsize=9,
    arrowprops=dict(arrowstyle="->", color="navy", lw=0.9),
)

ax1.set_title("1006R1-V normal TGA")
ax1.grid(True, which="major", linestyle="--", alpha=0.35)
ax1.legend(
    [line1, line2],
    [line1.get_label(), line2.get_label()],
    loc="best",
    frameon=True,
)

fig.tight_layout()
fig.savefig(out_dir / "1006R1-V_normal_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
