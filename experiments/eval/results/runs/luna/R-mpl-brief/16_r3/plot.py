from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/16_r3/out")
SHEET_NAME = "1006R1-V normal"

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
temperature = pd.to_numeric(df["Temperature"], errors="coerce")
weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
valid = temperature.notna() & weight.notna()
temperature = temperature[valid]
weight = weight[valid]

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(temperature, weight, color="#1f4e9c", linewidth=1.6, label="Weight")
ax.set_title(SHEET_NAME)
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.grid(True, alpha=0.3)

# 측정 온도가 800 °C에 가장 가까운 지점의 잔류량을 표시합니다.
residue_idx = (temperature - 800).abs().idxmin()
residue_temp = temperature.loc[residue_idx]
residue_weight = weight.loc[residue_idx]
ax.scatter([residue_temp], [residue_weight], color="#1f4e9c", zorder=3)
ax.annotate(
    f"Residue {residue_weight:.1f}%",
    xy=(residue_temp, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
)

ax.legend(loc="center left")
fig.tight_layout()
fig.savefig(OUT_DIR / "1006R1-V normal.png", dpi=300, bbox_inches="tight")
plt.close(fig)
