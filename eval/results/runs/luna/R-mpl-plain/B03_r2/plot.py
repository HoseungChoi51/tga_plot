from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B03_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

data = pd.read_csv(DATA_FILE)
data.columns = [str(column).strip() for column in data.columns]

frequency_col = "Angular frequency (rad/s)"
storage_col = "Storage modulus G' (Pa)"
loss_col = "Loss modulus G'' (Pa)"

for column in (frequency_col, storage_col, loss_col):
    data[column] = pd.to_numeric(data[column], errors="coerce")

data = data.dropna(subset=[frequency_col, storage_col, loss_col])
data = data[
    (data[frequency_col] > 0)
    & (data[storage_col] > 0)
    & (data[loss_col] > 0)
].sort_values(frequency_col)

fig, ax_left = plt.subplots(figsize=(8, 5.5))
ax_right = ax_left.twinx()

line_storage, = ax_left.plot(
    data[frequency_col],
    data[storage_col],
    marker="o",
    markersize=5,
    linewidth=2,
    color="#1f77b4",
    label="G' (저장 탄성률)",
)
line_loss, = ax_right.plot(
    data[frequency_col],
    data[loss_col],
    marker="s",
    markersize=5,
    linewidth=2,
    color="#d62728",
    label="G'' (손실 탄성률)",
)

ax_left.set_xscale("log")
ax_left.set_yscale("log")
ax_right.set_yscale("log")

ax_left.set_xlabel("각주파수 (rad/s)")
ax_left.set_ylabel("저장 탄성률 G' (Pa)", color="#1f77b4")
ax_right.set_ylabel("손실 탄성률 G'' (Pa)", color="#d62728")
ax_left.tick_params(axis="y", colors="#1f77b4")
ax_right.tick_params(axis="y", colors="#d62728")

for axis in (ax_left.xaxis, ax_left.yaxis, ax_right.yaxis):
    axis.set_major_locator(LogLocator(base=10))
    axis.set_major_formatter(LogFormatterMathtext(base=10))

ax_left.grid(True, which="both", linestyle="--", alpha=0.35)
ax_left.legend(
    [line_storage, line_loss],
    [line_storage.get_label(), line_loss.get_label()],
    loc="best",
    frameon=True,
)
ax_left.set_title("주파수에 따른 저장 탄성률과 손실 탄성률")
fig.tight_layout()

fig.savefig(OUT_DIR / "rheology_moduli_log.png", dpi=300, bbox_inches="tight")
plt.close(fig)
