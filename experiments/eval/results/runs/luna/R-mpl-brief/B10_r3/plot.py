from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B10_r3/out")

SHEET_NAME = "Annealed"
FIGSIZE = (3.5, 2.6)
DPI = 600
FONT_SIZE = 8


def find_column(columns, terms):
    """Find the first column whose name contains one of the given terms."""
    names = [str(name).strip() for name in columns]
    for term in terms:
        for name in names:
            if term.lower() in name.lower():
                return name
    raise ValueError(f"Could not find a column matching any of {terms!r}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    x_col = find_column(df.columns, ["Temperature"])
    weight_col = find_column(df.columns, ["Weight"])
    dtg_col = find_column(df.columns, ["Deriv. Weight", "DTG"])

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    temperature = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg = data[dtg_col].to_numpy()

    # TGA convention: invert DTG so mass-loss peaks point upward.
    dtg_plot = -dtg

    fig, ax1 = plt.subplots(figsize=FIGSIZE)
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(
        temperature, weight, color="black", linestyle="-", linewidth=1.1,
        label="Weight"
    )
    dtg_line, = ax2.plot(
        temperature, dtg_plot, color="black", linestyle="--", linewidth=1.0,
        label="DTG"
    )

    # Residue at the measured point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(temperature - 800.0)))
    ax1.plot(
        temperature[residue_idx], weight[residue_idx], marker="o",
        markersize=3.5, markerfacecolor="white", markeredgecolor="black",
        linestyle="none"
    )
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        xy=(temperature[residue_idx], weight[residue_idx]),
        xytext=(4, 5), textcoords="offset points",
        fontsize=FONT_SIZE, color="black"
    )

    # Highest upward DTG peak above 150 °C.
    eligible = np.flatnonzero(temperature > 150.0)
    if eligible.size:
        peak_idx = int(eligible[np.argmax(dtg_plot[eligible])])
        ax2.plot(
            temperature[peak_idx], dtg_plot[peak_idx], marker="s",
            markersize=3.5, markerfacecolor="white", markeredgecolor="black",
            linestyle="none"
        )
        ax2.annotate(
            f"{temperature[peak_idx]:.0f} °C",
            xy=(temperature[peak_idx], dtg_plot[peak_idx]),
            xytext=(4, -10), textcoords="offset points",
            fontsize=FONT_SIZE, color="black"
        )

    ax1.set_title(SHEET_NAME, fontsize=FONT_SIZE)
    ax1.set_xlabel("Temperature (°C)", fontsize=FONT_SIZE)
    ax1.set_ylabel("Weight (%)", fontsize=FONT_SIZE)
    ax2.set_ylabel("DTG (%/°C)", fontsize=FONT_SIZE)

    for axis in (ax1, ax2):
        axis.tick_params(axis="both", labelsize=FONT_SIZE, colors="black")
        axis.spines["top"].set_color("black")
    ax1.spines["left"].set_color("black")
    ax1.spines["bottom"].set_color("black")
    ax2.spines["right"].set_color("black")

    ax1.legend(
        [weight_line, dtg_line], ["Weight", "DTG"],
        loc="center left", fontsize=FONT_SIZE, frameon=False
    )

    fig.tight_layout()
    output_path = OUT_DIR / "Annealed.png"
    fig.savefig(output_path, dpi=DPI, format="png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
