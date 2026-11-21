from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/07_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

fig, ax = plt.subplots(figsize=(9, 6))
ax_derivative = ax.twinx()

for sheet_name, df in sheets.items():
    df.columns = [str(column).strip() for column in df.columns]
    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

    valid_weight = temperature.notna() & weight.notna()
    valid_derivative = temperature.notna() & derivative.notna()

    ax.plot(
        temperature[valid_weight],
        weight[valid_weight],
        label=f"{sheet_name} Weight",
    )
    ax_derivative.plot(
        temperature[valid_derivative],
        derivative[valid_derivative],
        linestyle="--",
        label=f"{sheet_name} D.W.",
    )

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax_derivative.set_ylabel("D.W. (%/°C)")
ax.set_title("TGA")
ax.grid(True, alpha=0.3)

handles1, labels1 = ax.get_legend_handles_labels()
handles2, labels2 = ax_derivative.get_legend_handles_labels()
ax.legend(
    handles1 + handles2,
    labels1 + labels2,
    loc="upper right",
    fontsize=9,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "TGA.png", dpi=300, bbox_inches="tight")
plt.close(fig)
