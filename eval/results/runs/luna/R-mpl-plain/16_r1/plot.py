from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/16_r1/out")
SHEET_NAME = "1006R1-V normal"

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(column).strip() for column in df.columns]

temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
valid = temperature.notna() & weight.notna()

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(temperature[valid], weight[valid], color="#1f77b4", linewidth=1.8)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title(SHEET_NAME)
ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)

fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V_normal_weight.png", dpi=300, bbox_inches="tight")
plt.close(fig)
