from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B23_r3/out")

SAMPLES = [
    ("Raw", "black"),
    ("Acid-washed", "blue"),
    ("Annealed", "red"),
]

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = ["Noto Sans CJK KR", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9, 6))

    for sheet, color in SAMPLES:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        ax.plot(
            df["Temperature (°C)"],
            df["Weight (%)"],
            color=color,
            linewidth=2,
            label=sheet,
        )

    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%)")
    ax.set_xlim(30, 900)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "overlaid_weight_vs_temperature.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
