from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/21_r1/out"

# Read the worksheet using the header at Excel row 8.
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=7, engine="openpyxl")

# Excel columns C, D, and E correspond to these named data columns.
x = pd.to_numeric(df["Temperature"], errors="coerce")
y1 = pd.to_numeric(df["Weight(%)"], errors="coerce")
y2 = pd.to_numeric(df["D.W(%/C)"], errors="coerce")
data = pd.DataFrame({"x": x, "y1": y1, "y2": y2}).dropna()

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1 = ax1.plot(data["x"], data["y1"], color="tab:blue", linewidth=1.8, label="Weight(%)")
line2 = ax2.plot(data["x"], data["y2"], color="tab:red", linewidth=1.5, label="D.W(%/C)")

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="tab:blue")
ax2.set_ylabel("D.W (%/°C)", color="tab:red")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax2.tick_params(axis="y", labelcolor="tab:red")
ax1.grid(True, linestyle="--", alpha=0.35)

lines = line1 + line2
ax1.legend(lines, [line.get_label() for line in lines], loc="best")
fig.tight_layout()

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "tga_plot.png", dpi=300, bbox_inches="tight")
plt.close(fig)
