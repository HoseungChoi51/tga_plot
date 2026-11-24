from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B17_r3/out"

SHEETS = ["PE", "PVC", "PET"]
COLORS = {"PE": "#0072B2", "PVC": "#D55E00", "PET": "#009E73"}
# Curves are separated by 20 percentage points, with PE as the baseline.
OFFSETS = {"PE": 0, "PVC": 20, "PET": 40}

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9, 6))

    for sheet in SHEETS:
        df = pd.read_excel(DATA_FILE, sheet_name=sheet)
        x = pd.to_numeric(df["Temperature (°C)"], errors="coerce")
        weight = pd.to_numeric(df["Weight (%)"], errors="coerce")
        offset = OFFSETS[sheet]

        ax.plot(
            x,
            weight + offset,
            color=COLORS[sheet],
            linewidth=2,
            label=f"{sheet} (offset +{offset}%)" if offset else sheet,
        )

    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%) + vertical offset")
    ax.set_title("TGA 무게 곡선")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_dir / "polymer_weight_offset.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
