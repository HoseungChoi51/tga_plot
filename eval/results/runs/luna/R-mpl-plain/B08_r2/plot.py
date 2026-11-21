from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B08_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="Raw")
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col)

temperature = pd.to_numeric(df[temperature_col], errors="coerce")
weight = pd.to_numeric(df[weight_col], errors="coerce")
valid = temperature.notna() & weight.notna()

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(temperature[valid], weight[valid], color="#1f77b4", linewidth=1.8)
ax.axhline(50, color="0.35", linestyle="--", linewidth=1.2, label="무게 50%")

ax.text(
    0.97, 0.97, "공기, 10 °C/min",
    transform=ax.transAxes,
    ha="right", va="top",
    fontsize=11,
)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_xlim(temperature[valid].min(), temperature[valid].max())
ax.set_ylim(0, 105)
ax.grid(True, linestyle=":", linewidth=0.7, alpha=0.7)
ax.legend(loc="best", frameon=False)
fig.tight_layout()

fig.savefig(OUT_DIR / "raw_weight_50_percent.png", dpi=300, bbox_inches="tight")
plt.close(fig)
