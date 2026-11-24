from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B03_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read and clean the CSV data.
df = pd.read_csv(DATA_FILE)
df.columns = [str(column).strip() for column in df.columns]

x_col = "Angular frequency (rad/s)"
g_storage_col = "Storage modulus G' (Pa)"
g_loss_col = "Loss modulus G'' (Pa)"

for column in (x_col, g_storage_col, g_loss_col):
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df[[x_col, g_storage_col, g_loss_col]].dropna()
df = df[
    (df[x_col] > 0)
    & (df[g_storage_col] > 0)
    & (df[g_loss_col] > 0)
].sort_values(x_col)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(8, 5))
ax2 = ax1.twinx()

line1, = ax1.plot(
    df[x_col], df[g_storage_col],
    color="#1f4e9c", marker="o", linewidth=2,
    label="Storage modulus G' (Pa)",
)
line2, = ax2.plot(
    df[x_col], df[g_loss_col],
    color="#c0392b", marker="s", linewidth=2,
    label="Loss modulus G'' (Pa)",
)

ax1.set_xscale("log")
ax1.set_yscale("log")
ax2.set_yscale("log")

ax1.set_xlabel("Angular frequency (rad/s)")
ax1.set_ylabel("Storage modulus G' (Pa)", color="#1f4e9c")
ax2.set_ylabel("Loss modulus G'' (Pa)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.set_title("Rheology")
ax1.grid(True, which="both", linestyle="--", alpha=0.35)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")

fig.tight_layout()
fig.savefig(OUT_DIR / "rheology.png", dpi=300, bbox_inches="tight")
plt.close(fig)
