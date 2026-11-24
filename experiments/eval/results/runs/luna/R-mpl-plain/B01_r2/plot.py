from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B01_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and identify the temperature and weight columns.
df = pd.read_csv(DATA_FILE)
temperature_col = next(c for c in df.columns if "Temperature" in str(c))
weight_col = next(c for c in df.columns if "Weight (%)" in str(c))

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature, weight = temperature[valid], weight[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(temperature, weight, color="black", linewidth=1.5, label="Weight")

regions = [
    (120, 250, "H₂O", "#6baed6"),
    (430, 580, "CO", "#74c476"),
    (640, 830, "CO₂", "#fd8d3c"),
]
y_top = float(weight.max())

for x0, x1, label, color in regions:
    ax.axvspan(x0, x1, color=color, alpha=0.22, linewidth=0)
    ax.text(
        (x0 + x1) / 2,
        y_top + 1.2,
        label,
        ha="center",
        va="bottom",
        fontsize=12,
        color=color,
        fontweight="bold",
    )

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_xlim(float(temperature.min()), float(temperature.max()))
ax.set_ylim(float(weight.min()) - 2, y_top + 7)
ax.grid(True, alpha=0.25)
fig.tight_layout()

fig.savefig(OUT_DIR / "caox_mass_loss_regions.png", dpi=300, bbox_inches="tight")
plt.close(fig)
