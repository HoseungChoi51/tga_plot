from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/21_r2/out"

# The workbook has blank rows above its header; read the header from Excel row 8.
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=7, engine="openpyxl")

# Select columns by their worksheet positions: C = X, D = Y1, E = Y2.
x = pd.to_numeric(df.iloc[:, 2], errors="coerce")
y1 = pd.to_numeric(df.iloc[:, 3], errors="coerce")
y2 = pd.to_numeric(df.iloc[:, 4], errors="coerce")
data = pd.DataFrame({"x": x, "y1": y1, "y2": y2}).dropna()

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
fig, ax1 = plt.subplots(figsize=(10, 6))

line1 = ax1.plot(data["x"], data["y1"], color="tab:blue", label="D행 (Weight %)")
ax1.set_xlabel("C행 (Temperature)")
ax1.set_ylabel("D행 (Weight %)", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
line2 = ax2.plot(data["x"], data["y2"], color="tab:red", label="E행 (D.W %/C)")
ax2.set_ylabel("E행 (D.W %/C)", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

lines = line1 + line2
ax1.legend(lines, [line.get_label() for line in lines], loc="best")
ax1.set_title("Temperature에 따른 Weight 및 D.W 변화")
fig.tight_layout()
fig.savefig(out_dir / "tga_plot.png", dpi=300, bbox_inches="tight")
plt.close(fig)
