from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/05_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(col for col in df.columns if "temperature" in col.lower())
    weight_col = next(col for col in df.columns if "weight" in col.lower())
    derivative_col = next(
        col for col in df.columns
        if "d.w" in col.lower() or "dw(" in col.lower() or "derivative" in col.lower()
    )

    data = df[[temperature_col, weight_col, derivative_col]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        data[temperature_col],
        data[weight_col],
        color="black",
        linewidth=2.5,
        label=weight_col,
    )
    line2, = ax2.plot(
        data[temperature_col],
        data[derivative_col],
        linestyle="--",
        label=derivative_col,
    )

    ax1.set_xlabel(temperature_col)
    ax1.set_ylabel(weight_col, color=line1.get_color())
    ax2.set_ylabel(derivative_col, color=line2.get_color())
    ax1.set_title(sheet_name)
    ax1.grid(True, alpha=0.3)
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")

    fig.tight_layout()
    output_name = "".join(
        char if char.isalnum() or char in "-_ ." else "_" for char in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
