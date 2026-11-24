from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B17_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
fig, ax = plt.subplots(figsize=(9, 6))

colors = ["#1f4e9c", "#c0392b", "#2e8b57"]
offset_step = 20

for index, (sheet_name, df) in enumerate(sheets.items()):
    # Use the temperature and weight columns identified from the workbook headers.
    temperature_col = next(
        (col for col in df.columns if "temperature" in str(col).lower()), df.columns[1]
    )
    weight_col = next(
        (col for col in df.columns if "weight" in str(col).lower()
         and "deriv" not in str(col).lower()),
        df.columns[2],
    )

    data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
    offset = index * offset_step
    ax.plot(
        data[temperature_col],
        data[weight_col] + offset,
        color=colors[index % len(colors)],
        linewidth=1.8,
        label=f"{sheet_name} (+{offset}%)" if offset else str(sheet_name),
    )

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%) + vertical offset")
ax.set_title("Weight curves with 20% vertical offsets")
ax.legend(loc="best", frameon=False)
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(OUT_DIR / "overlaid_weight_curves_offset.png", dpi=300, bbox_inches="tight")
plt.close(fig)
