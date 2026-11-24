from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/01_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

fig, ax_weight = plt.subplots(figsize=(10, 6))
ax_derivative = ax_weight.twinx()
colors = plt.get_cmap("tab10").colors

for i, (sheet_name, df) in enumerate(sheets.items()):
    df.columns = [str(col).strip() for col in df.columns]
    required = ["Temperature", "Weight(%)", "D.W(%/C)"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{sheet_name} 시트에 필요한 열이 없습니다: {missing}")

    data = df[required].apply(pd.to_numeric, errors="coerce").dropna()
    color = colors[i % len(colors)]
    ax_weight.plot(
        data["Temperature"],
        data["Weight(%)"],
        color=color,
        linewidth=1.8,
        label=f"{sheet_name} — Weight",
    )
    ax_derivative.plot(
        data["Temperature"],
        data["D.W(%/C)"],
        color=color,
        linewidth=1.4,
        linestyle="--",
        alpha=0.85,
        label=f"{sheet_name} — D.W",
    )

ax_weight.set_xlabel("Temperature (°C)")
ax_weight.set_ylabel("Weight (%)")
ax_derivative.set_ylabel("D.W (%/°C)")
ax_weight.set_title("TGA Curves")
ax_weight.grid(True, linestyle=":", alpha=0.45)

lines1, labels1 = ax_weight.get_legend_handles_labels()
lines2, labels2 = ax_derivative.get_legend_handles_labels()
ax_weight.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc="best",
    fontsize=8,
    frameon=True,
)

fig.tight_layout()
fig.savefig(OUT_DIR / "TGA_curves.png", dpi=300, bbox_inches="tight")
plt.close(fig)
