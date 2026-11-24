from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoLocator, MaxNLocator
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/09_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

excel = pd.ExcelFile(DATA_FILE)
for sheet_name in excel.sheet_names:
    data = pd.read_excel(excel, sheet_name=sheet_name)
    data.columns = [str(col).strip() for col in data.columns]

    required = {"Temperature", "Weight(%)", "D.W(%/C)"}
    if not required.issubset(data.columns):
        continue

    plot_data = data[["Temperature", "Weight(%)", "D.W(%/C)"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    if plot_data.empty:
        continue

    fig, ax_weight = plt.subplots(figsize=(8, 5))
    ax_derivative = ax_weight.twinx()

    ax_weight.plot(
        plot_data["Temperature"],
        plot_data["Weight(%)"],
        color="tab:blue",
        linewidth=1.8,
        label="Weight (%)",
    )
    ax_derivative.plot(
        plot_data["Temperature"],
        plot_data["D.W(%/C)"],
        color="tab:red",
        linewidth=1.5,
        label="D.W (%/°C)",
    )

    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="tab:blue")
    ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
    ax_weight.tick_params(axis="y", labelcolor="tab:blue")
    ax_derivative.tick_params(axis="y", labelcolor="tab:red")

    for axis in (ax_weight, ax_derivative):
        axis.tick_params(which="both", direction="out", labelsize=9)
        axis.xaxis.set_major_locator(MaxNLocator(nbins=8))
    ax_weight.yaxis.set_major_locator(AutoLocator())
    ax_derivative.yaxis.set_major_locator(AutoLocator())

    ax_weight.set_title(sheet_name)
    ax_weight.grid(True, linestyle="--", alpha=0.3)

    lines = ax_weight.get_lines() + ax_derivative.get_lines()
    ax_weight.legend(lines, [line.get_label() for line in lines], loc="best", frameon=False)

    fig.tight_layout()
    output_name = "".join(
        char if char.isalnum() or char in "-_ ." else "_" for char in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
