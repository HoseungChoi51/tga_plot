from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/11_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

fig, ax_weight = plt.subplots(figsize=(10, 6))
ax_derivative = ax_weight.twinx()

colors = ["#1f77b4", "#d62728", "#2ca02c"]

for (sheet_name, data), color in zip(sheets.items(), colors):
    data.columns = [str(column).strip() for column in data.columns]
    temperature = pd.to_numeric(data["Temperature"], errors="coerce")
    weight = pd.to_numeric(data["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(data["D.W(%/C)"], errors="coerce")
    valid = temperature.notna() & weight.notna() & derivative.notna()

    # 피크 마커나 피크 주석 없이 TGA 및 DTG 곡선만 표시
    ax_weight.plot(
        temperature[valid],
        weight[valid],
        color=color,
        linewidth=2,
        label=f"{sheet_name} — Weight",
    )
    ax_derivative.plot(
        temperature[valid],
        derivative[valid],
        color=color,
        linewidth=1.5,
        linestyle="--",
        alpha=0.8,
        label=f"{sheet_name} — DTG",
    )

ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)")
ax_derivative.set_ylabel("D.W (%/°C)")
ax_weight.set_title("TGA and DTG Curves")
ax_weight.set_xlim(left=30)
ax_weight.grid(True, linestyle=":", alpha=0.45)

handles1, labels1 = ax_weight.get_legend_handles_labels()
handles2, labels2 = ax_derivative.get_legend_handles_labels()
ax_weight.legend(handles1 + handles2, labels1 + labels2, loc="best", fontsize=8)

fig.tight_layout()
fig.savefig(OUT_DIR / "TGA_curves.png", dpi=300, bbox_inches="tight")
plt.close(fig)
