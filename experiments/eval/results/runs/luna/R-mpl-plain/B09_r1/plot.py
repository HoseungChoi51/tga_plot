from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B09_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the PE sheet and identify columns by their header names.
df = pd.read_excel(DATA_FILE, sheet_name="PE")
df.columns = [str(col).strip() for col in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col and "Deriv" not in col)
derivative_col = next(col for col in df.columns if "Deriv" in col)

for col in (temperature_col, weight_col, derivative_col):
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=[temperature_col, weight_col, derivative_col])

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(
    df[temperature_col],
    df[weight_col],
    color="red",
    linewidth=3,
    label=weight_col,
)
ax1.set_xlabel(temperature_col)
ax1.set_ylabel(weight_col, color="red")
ax1.tick_params(axis="y", labelcolor="red")
ax1.set_xlim(100, 700)
ax1.xaxis.set_major_locator(MultipleLocator(100))
ax1.grid(True, linestyle="--", alpha=0.35)

ax2 = ax1.twinx()
ax2.plot(
    df[temperature_col],
    df[derivative_col],
    color="tab:blue",
    linewidth=1.8,
    label=derivative_col,
)
ax2.set_ylabel(derivative_col, color="tab:blue")
ax2.tick_params(axis="y", labelcolor="tab:blue")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

ax1.set_title("PE TGA")
fig.tight_layout()
fig.savefig(OUT_DIR / "PE_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
