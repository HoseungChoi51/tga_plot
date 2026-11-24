from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/04_r3/out")
SHEET_NAME = "1006R1-V normal"

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")
valid = temperature.notna() & weight.notna() & derivative.notna()

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

ax1.plot(
    temperature[valid],
    weight[valid],
    color="tab:blue",
    linewidth=2,
    label="Weight(%)",
)
ax2.plot(
    temperature[valid],
    derivative[valid],
    color="tab:red",
    linewidth=1.8,
    label="D.W(%/C)",
)

ax1.set_title("CNT 산화 거동", fontsize=18, color="navy", pad=12)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("D.W (%/°C)")
ax1.grid(True, linestyle="--", alpha=0.4)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

fig.tight_layout()
fig.savefig(OUT_DIR / "CNT_산화_거동.png", dpi=300, bbox_inches="tight")
plt.close(fig)
