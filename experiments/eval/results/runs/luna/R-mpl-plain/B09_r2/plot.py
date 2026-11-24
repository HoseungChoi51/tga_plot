from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B09_r2/out"

# Korean-capable font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name="PE")
df.columns = [str(column).strip() for column in df.columns]

x_col = "Temperature (°C)"
y1_col = "Weight (%)"

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(
    df[x_col],
    df[y1_col],
    color="red",
    linewidth=3,
    label=y1_col,
)

ax.set_xlim(100, 700)
ax.xaxis.set_major_locator(MultipleLocator(100))
ax.set_xlabel(x_col)
ax.set_ylabel(y1_col)
ax.set_title("PE TGA")
ax.grid(True, linestyle="--", alpha=0.35)
ax.legend()
fig.tight_layout()

fig.savefig(out_dir / "PE_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
