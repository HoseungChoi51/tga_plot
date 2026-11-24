from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B20_r1/out")
SHEET_NAME = "Acid-washed"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
    temperature = pd.to_numeric(data["Temperature (°C)"], errors="coerce")
    weight = pd.to_numeric(data["Weight (%)"], errors="coerce")
    deriv_weight = pd.to_numeric(data["Deriv. Weight (%/°C)"], errors="coerce")

    valid = temperature.notna()
    temperature = temperature[valid]
    weight = weight[valid]
    deriv_weight = deriv_weight[valid]

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax_weight = plt.subplots(figsize=(9, 6))
    ax_deriv = ax_weight.twinx()

    line_weight, = ax_weight.plot(
        temperature, weight, color="#1f77b4", linewidth=2, label="Weight"
    )
    line_deriv, = ax_deriv.plot(
        temperature, deriv_weight, color="#d62728", linewidth=1.8,
        label="Derivative weight"
    )

    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="#1f77b4")
    ax_deriv.set_ylabel("Deriv. Weight (%/°C)", color="#d62728")
    ax_weight.tick_params(axis="y", labelcolor="#1f77b4")
    ax_deriv.tick_params(axis="y", labelcolor="#d62728")

    ax_weight.set_xlim(30, 900)
    ax_weight.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax_weight.tick_params(axis="x", which="minor", length=3, color="0.35")
    ax_weight.tick_params(axis="x", which="major", length=6)

    ax_weight.grid(True, which="major", axis="both", linestyle="--", alpha=0.35)
    ax_weight.grid(True, which="minor", axis="x", linestyle=":", alpha=0.2)
    ax_weight.legend(
        [line_weight, line_deriv],
        [line_weight.get_label(), line_deriv.get_label()],
        loc="best",
    )
    ax_weight.set_title("Acid-washed TGA")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "acid_washed_tga.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
