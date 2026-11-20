from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/16_r2/out"
SHEET_NAME = "1006R1-V normal"

# Korean font and plot styling
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

data = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
data.columns = [str(column).strip() for column in data.columns]

temperature = pd.to_numeric(data["Temperature"], errors="coerce")
weight = pd.to_numeric(data["Weight(%)"], errors="coerce")
valid = temperature.notna() & weight.notna()

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(temperature[valid], weight[valid], color="#1f77b4", linewidth=1.8)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title(SHEET_NAME)
ax.grid(True, linestyle="--", alpha=0.35)

fig.tight_layout()
out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "1006R1-V_normal_weight.png", dpi=300, bbox_inches="tight")
plt.close(fig)
