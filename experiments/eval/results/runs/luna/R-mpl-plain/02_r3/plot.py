from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/02_r3/out")
SHEET_NAME = "1006R1-V normal"
OUTPUT_FILE = OUT_DIR / "1006R1-V_normal_TGA.png"

# Korean-capable font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

# Use the requested B, C, and D columns: Temperature, Weight(%), and D.W(%/C).
temperature = pd.to_numeric(df.iloc[:, 1], errors="coerce")
weight = pd.to_numeric(df.iloc[:, 2], errors="coerce")
deriv_weight = pd.to_numeric(df.iloc[:, 3], errors="coerce")
data = pd.DataFrame(
    {"Temperature": temperature, "Weight": weight, "DerivWeight": deriv_weight}
).dropna()

x = data["Temperature"].to_numpy()
y1 = data["Weight"].to_numpy()
y2 = data["DerivWeight"].to_numpy()

# Locate the measured temperature closest to 800 °C and its corresponding residue.
residue_idx = int(np.argmin(np.abs(x - 800)))
residue_temperature = x[residue_idx]
residue_value = y1[residue_idx]

# Mark the minimum Deriv.Weight value (the largest-magnitude negative derivative).
deriv_min_idx = int(np.argmin(y2))
deriv_min_temperature = x[deriv_min_idx]
deriv_min_value = y2[deriv_min_idx]

OUT_DIR.mkdir(parents=True, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(x, y1, color="#1f77b4", linewidth=2, label="Weight")
line2, = ax2.plot(x, y2, color="#d62728", linewidth=1.6, label="Deriv.Weight")

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f77b4")
ax2.set_ylabel("Deriv.Weight (%/°C)", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#d62728")

# Temperature ticks begin at 0 and increase by 200 °C.
x_max = max(900, int(np.ceil(np.nanmax(x) / 200) * 200))
ax1.set_xlim(0, x_max)
ax1.set_xticks(np.arange(0, x_max + 1, 200))

# Weight ticks every 20%, and derivative ticks every 0.2.
ax1.set_ylim(0, 100)
ax1.set_yticks(np.arange(0, 101, 20))

deriv_min = float(np.nanmin(y2))
deriv_max = float(np.nanmax(y2))
lower = np.floor(deriv_min / 0.2) * 0.2
upper = np.ceil(deriv_max / 0.2) * 0.2
if lower == upper:
    upper += 0.2
ax2.set_ylim(lower, upper)
ax2.set_yticks(np.arange(lower, upper + 0.001, 0.2))

# Show the minimum Deriv.Weight value and its temperature.
ax2.scatter(
    [deriv_min_temperature], [deriv_min_value],
    color="#d62728", edgecolor="white", linewidth=0.8, zorder=5
)
ax2.annotate(
    f"Deriv.Weight min = {deriv_min_value:.3f} %/°C\n({deriv_min_temperature:.1f} °C)",
    xy=(deriv_min_temperature, deriv_min_value),
    xytext=(12, 12),
    textcoords="offset points",
    color="#a51d1d",
    fontsize=9,
    arrowprops={"arrowstyle": "->", "color": "#a51d1d"},
)

# Display residue at the measured temperature nearest 800 °C.
ax1.scatter(
    [residue_temperature], [residue_value],
    color="#1f77b4", edgecolor="white", linewidth=0.8, zorder=5
)
ax1.annotate(
    f"Residue {residue_value:.2f}%\n({residue_temperature:.1f} °C)",
    xy=(residue_temperature, residue_value),
    xytext=(10, -28),
    textcoords="offset points",
    color="#164f7a",
    fontsize=10,
    arrowprops={"arrowstyle": "->", "color": "#164f7a"},
)

ax1.set_title("1006R1-V normal TGA")
ax1.grid(True, which="major", linestyle="--", alpha=0.35)
ax1.legend([line1, line2], ["Weight", "Deriv.Weight"], loc="best")
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.close(fig)
