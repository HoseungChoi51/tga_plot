from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/22_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    temperature_col = next(col for col in df.columns if "Temperature" in col)
    weight_col = next(col for col in df.columns if "Weight" in col)
    derivative_col = next(
        col for col in df.columns
        if "D.W" in col or "dW" in col or "Derivative" in col
    )

    data = df[[temperature_col, weight_col, derivative_col]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(data[temperature_col], data[weight_col], color="tab:blue", linewidth=1.8)
    ax2.plot(data[temperature_col], data[derivative_col], color="green", linewidth=1.8)

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="tab:blue")
    ax2.set_ylabel("D.W (%/°C)", color="green")
    ax2.tick_params(axis="y", colors="green")

    ax1.set_title(sheet_name)
    ax1.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()

    filename = "".join(
        "_" if char in '<>:"/\\|?*' else char for char in sheet_name
    )
    fig.savefig(out_dir / f"{filename}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
