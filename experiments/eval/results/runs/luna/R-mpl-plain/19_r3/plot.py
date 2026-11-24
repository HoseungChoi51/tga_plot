from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/19_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean font and requested typography
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": 13,
    "text.color": "gray",
    "axes.labelcolor": "gray",
    "axes.edgecolor": "gray",
    "xtick.color": "gray",
    "ytick.color": "gray",
    "legend.labelcolor": "gray",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]
    required = {"Temperature", "Weight(%)", "D.W(%/C)"}
    if not required.issubset(df.columns):
        continue

    data = df[["Temperature", "Weight(%)", "D.W(%/C)"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    fig, ax_weight = plt.subplots(figsize=(9, 6))
    ax_derivative = ax_weight.twinx()

    weight_line, = ax_weight.plot(
        data["Temperature"], data["Weight(%)"],
        color="#2878B5", linewidth=2, label="Weight(%)"
    )
    derivative_line, = ax_derivative.plot(
        data["Temperature"], data["D.W(%/C)"],
        color="#D65F5F", linewidth=1.8, label="D.W(%/C)"
    )

    ax_weight.set_xlabel("Temperature (°C)", color="gray")
    ax_weight.set_ylabel("Weight (%)", color="gray")
    ax_derivative.set_ylabel("D.W (%/°C)", color="gray")
    ax_weight.set_title(sheet_name, color="gray")
    ax_weight.tick_params(axis="both", colors="gray")
    ax_derivative.tick_params(axis="y", colors="gray")

    for spine in ax_weight.spines.values():
        spine.set_color("gray")
    for spine in ax_derivative.spines.values():
        spine.set_color("gray")

    ax_weight.grid(True, linestyle="--", alpha=0.25, color="gray")
    ax_weight.legend(
        [weight_line, derivative_line],
        ["Weight(%)", "D.W(%/C)"],
        loc="best",
        frameon=False,
    )

    fig.tight_layout()
    safe_name = "".join(
        char if char.isalnum() or char in "-_ " else "_"
        for char in str(sheet_name)
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
