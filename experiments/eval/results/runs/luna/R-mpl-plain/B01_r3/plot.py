from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B01_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and locate the temperature and weight columns.
df = pd.read_csv(DATA_FILE)
temperature_col = next(c for c in df.columns if "Temperature" in str(c))
weight_col = next(c for c in df.columns if "Weight (%)" in str(c))

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid]
weight = weight[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(temperature, weight, color="#222222", linewidth=1.8)

regions = [
    (120, 250, "H2O", "#75b9e7"),
    (430, 580, "CO", "#e89b72"),
    (640, 830, "CO2", "#8fc79a"),
]

for left, right, label, color in regions:
    ax.axvspan(left, right, color=color, alpha=0.23, linewidth=0)
    ax.text(
        (left + right) / 2,
        1.025,
        label,
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color="#333333",
        clip_on=False,
    )

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_xlim(temperature.min(), temperature.max())
ax.grid(True, alpha=0.22)
ax.margins(y=0.12)
fig.tight_layout()

fig.savefig(OUT_DIR / "caox_mass_loss_regions.png", dpi=300, bbox_inches="tight")
plt.close(fig)
