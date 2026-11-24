from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B10_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the requested sheet and identify columns from their header names.
df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
df.columns = [str(column).strip() for column in df.columns]

temperature_col = next(col for col in df.columns if "Temperature" in col)
weight_col = next(col for col in df.columns if "Weight (%)" in col and "Deriv" not in col)
derivative_col = next(col for col in df.columns if "Deriv" in col and "Weight" in col)

for col in (temperature_col, weight_col, derivative_col):
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=[temperature_col, weight_col, derivative_col])

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

fig, ax = plt.subplots(figsize=(3.5, 2.6), constrained_layout=True)
ax_deriv = ax.twinx()

# Black-and-white presentation: solid line for TGA, dashed line for derivative.
line_tga, = ax.plot(
    df[temperature_col], df[weight_col],
    color="black", linestyle="-", linewidth=1.1, label="Weight"
)
line_deriv, = ax_deriv.plot(
    df[temperature_col], df[derivative_col],
    color="black", linestyle="--", linewidth=1.0, label="Deriv. weight"
)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax_deriv.set_ylabel("Deriv. weight (%/°C)")
ax.set_xlim(df[temperature_col].min(), df[temperature_col].max())

ax.tick_params(which="both", top=True, right=True)
ax_deriv.tick_params(which="both", direction="in")
ax.legend(
    handles=[line_tga, line_deriv],
    loc="best",
    frameon=False,
    handlelength=2.2,
)

for spine in ax.spines.values():
    spine.set_color("black")
for spine in ax_deriv.spines.values():
    spine.set_color("black")

output_file = OUT_DIR / "annealed_tga_bw.png"
fig.savefig(output_file, dpi=600, bbox_inches="tight", facecolor="white")
plt.close(fig)
