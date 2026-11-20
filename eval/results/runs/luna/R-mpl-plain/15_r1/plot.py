from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/15_r1/out"

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    sheets = pd.read_excel(DATA_FILE, sheet_name=None)
    fig, ax = plt.subplots(figsize=(10, 6))

    for sheet_name, df in sheets.items():
        df.columns = [str(column).strip() for column in df.columns]
        temperature_col = next(
            (column for column in df.columns if "temperature" in column.lower()),
            None,
        )
        weight_col = next(
            (column for column in df.columns if "weight" in column.lower()),
            None,
        )
        if temperature_col is None or weight_col is None:
            continue

        data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
        ax.plot(data[temperature_col], data[weight_col], linewidth=1.8, label=sheet_name)

    ax.set_title("TGA — 전체 시트")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(title="시트", frameon=True)
    fig.tight_layout()

    fig.savefig(out_dir / "TGA_all_sheets.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
