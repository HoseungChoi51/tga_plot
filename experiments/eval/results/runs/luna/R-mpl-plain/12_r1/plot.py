from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/12_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
colors = ["#1f77b4", "#d62728", "#2ca02c"]

fig, ax = plt.subplots(figsize=(9, 6))

for (sheet_name, data), color in zip(sheets.items(), colors):
    data.columns = [str(column).strip() for column in data.columns]
    temperature_col = next(col for col in data.columns if "temperature" in col.lower())
    weight_col = next(col for col in data.columns if "weight" in col.lower())

    temperature = pd.to_numeric(data[temperature_col], errors="coerce")
    weight = pd.to_numeric(data[weight_col], errors="coerce")
    valid = temperature.notna() & weight.notna()

    ax.plot(temperature[valid], weight[valid], label=sheet_name, color=color, linewidth=1.8)

ax.axvline(450, color="black", linestyle="--", linewidth=1.4)
ax.text(
    450,
    0.97,
    "산화 시작",
    transform=ax.get_xaxis_transform(),
    rotation=90,
    ha="right",
    va="top",
    fontsize=11,
    color="black",
    backgroundcolor="white",
)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA")
ax.set_xlim(left=30)
ax.grid(True, alpha=0.25)
ax.legend(title="Sample", frameon=False)
fig.tight_layout()

fig.savefig(OUT_DIR / "TGA_oxidation_start.png", dpi=300, bbox_inches="tight")
plt.close(fig)
