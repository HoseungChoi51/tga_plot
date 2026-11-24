from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/24_r2/out"

# Read the workbook sheet and use the temperature, weight, and heat-flow columns.
df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")
temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
heat_flow = pd.to_numeric(df["Heat Flow (W/g)"], errors="coerce")
valid = temperature.notna() & weight.notna() & heat_flow.notna()
temperature, weight, heat_flow = temperature[valid], weight[valid], heat_flow[valid]

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(
    temperature, weight, color="#1f77b4", linewidth=2, label="Weight (%)"
)
line2, = ax2.plot(
    temperature, heat_flow, color="#d62728", linewidth=1.8, label="Heat Flow (W/g)"
)

ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f77b4")
ax2.set_ylabel("Heat flow (W/g)", color="#d62728")
ax1.tick_params(axis="y", labelcolor="#1f77b4")
ax2.tick_params(axis="y", labelcolor="#d62728")

ax1.xaxis.set_minor_locator(AutoMinorLocator())
ax1.yaxis.set_minor_locator(AutoMinorLocator())
ax2.yaxis.set_minor_locator(AutoMinorLocator())
ax1.grid(True, which="major", linestyle="--", alpha=0.35)
ax1.grid(True, which="minor", linestyle=":", alpha=0.18)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")

fig.tight_layout()
out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "tga_heat_flow.png", dpi=300, bbox_inches="tight")
plt.close(fig)
