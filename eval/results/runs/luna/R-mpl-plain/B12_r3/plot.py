from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B12_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_FILE)
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col and "Deriv" not in col)

data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(temperature_col)

# Interpolate the weight at 900 °C for the residue label.
residue_900 = float(np.interp(900, data[temperature_col], data[weight_col]))

plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(data[temperature_col], data[weight_col], color="tab:blue", linewidth=2)

ax.set_xlim(100, 900)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA Weight Curve")
ax.grid(True, linestyle="--", alpha=0.35)

ax.scatter([900], [residue_900], color="tab:red", zorder=3)
ax.annotate(
    f"Residue at 900 °C: {residue_900:.2f}%",
    xy=(900, residue_900),
    xytext=(-12, 12),
    textcoords="offset points",
    ha="right",
    va="bottom",
    color="tab:red",
    arrowprops={"arrowstyle": "->", "color": "tab:red", "lw": 1},
)

fig.tight_layout()
fig.savefig(OUT_DIR / "caox_weight_curve.png", dpi=300, bbox_inches="tight")
plt.close(fig)
