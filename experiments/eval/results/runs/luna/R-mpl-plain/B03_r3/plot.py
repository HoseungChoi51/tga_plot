from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B03_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read the CSV and use its descriptive column headers.
data = pd.read_csv(DATA_FILE)
data.columns = data.columns.astype(str).str.strip()

x_col = "Angular frequency (rad/s)"
g_storage_col = "Storage modulus G' (Pa)"
g_loss_col = "Loss modulus G'' (Pa)"

# Keep only finite, positive values because all axes use logarithmic scales.
for col in (x_col, g_storage_col, g_loss_col):
    data[col] = pd.to_numeric(data[col], errors="coerce")

data = data.dropna(subset=[x_col, g_storage_col, g_loss_col])
data = data[
    (data[x_col] > 0)
    & (data[g_storage_col] > 0)
    & (data[g_loss_col] > 0)
].sort_values(x_col)

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "axes.unicode_minus": False,
    "font.size": 11,
})

fig, ax_left = plt.subplots(figsize=(8, 5.5))
ax_right = ax_left.twinx()

line_storage, = ax_left.plot(
    data[x_col],
    data[g_storage_col],
    marker="o",
    markersize=5,
    linewidth=2,
    color="#1f77b4",
    label="G' (저장 탄성률)",
)
line_loss, = ax_right.plot(
    data[x_col],
    data[g_loss_col],
    marker="s",
    markersize=5,
    linewidth=2,
    color="#d62728",
    label="G'' (손실 탄성률)",
)

ax_left.set_xscale("log")
ax_left.set_yscale("log")
ax_right.set_yscale("log")

ax_left.set_xlabel("Angular frequency (rad/s)")
ax_left.set_ylabel("Storage modulus G' (Pa)", color="#1f77b4")
ax_right.set_ylabel("Loss modulus G'' (Pa)", color="#d62728")
ax_left.tick_params(axis="y", colors="#1f77b4")
ax_right.tick_params(axis="y", colors="#d62728")

ax_left.grid(True, which="both", linestyle="--", linewidth=0.6, alpha=0.5)
ax_left.legend(
    [line_storage, line_loss],
    [line_storage.get_label(), line_loss.get_label()],
    loc="best",
    frameon=True,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "rheology_moduli_vs_frequency.png", dpi=300, bbox_inches="tight")
plt.close(fig)
