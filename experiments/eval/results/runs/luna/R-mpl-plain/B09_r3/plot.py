from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B09_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

data = pd.read_excel(DATA_FILE, sheet_name="PE")
temperature = pd.to_numeric(data["Temperature (°C)"], errors="coerce")
weight = pd.to_numeric(data["Weight (%)"], errors="coerce")
derivative = pd.to_numeric(data["Deriv. Weight (%/°C)"], errors="coerce")

fig, ax1 = plt.subplots(figsize=(9, 6))
ax1.plot(temperature, weight, color="red", linewidth=3, label="Weight (%)")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax1.set_xlim(100, 700)
ax1.set_xticks(range(100, 701, 100))
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(
    temperature,
    derivative,
    color="tab:blue",
    linewidth=1.5,
    label="Deriv. Weight (%/°C)",
)
ax2.set_ylabel("Deriv. Weight (%/°C)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

ax1.set_title("PE TGA")
fig.tight_layout()
fig.savefig(OUT_DIR / "PE_TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
