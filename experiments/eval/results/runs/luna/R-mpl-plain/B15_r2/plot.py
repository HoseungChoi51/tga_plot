from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B15_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(9, 5.5))

for sheet_name in ("PE", "PVC", "PET"):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(
        column for column in df.columns if "Temperature" in column
    )
    weight_col = next(
        column for column in df.columns if "Weight (%)" in column
    )

    data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
    ax.plot(data[temperature_col], data[weight_col], linewidth=1.8, label=sheet_name)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA Curves")
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
ax.grid(True, linestyle="--", alpha=0.35)
ax.legend(title="Polymer", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

fig.tight_layout()
fig.savefig(OUT_DIR / "polymers_tga_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
