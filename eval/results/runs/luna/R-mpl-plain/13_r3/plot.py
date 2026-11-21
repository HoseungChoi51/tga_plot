from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/13_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(column).strip() for column in df.columns]

    x_col = next(
        (column for column in df.columns if "Temperature" in column),
        None,
    )
    y_col = next(
        (column for column in df.columns if "Weight (mg)" in column),
        None,
    )

    if x_col is None or y_col is None:
        continue

    plot_data = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if plot_data.empty:
        continue

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(plot_data[x_col], plot_data[y_col], color="black", linewidth=1.5)
    ax.set_xlabel(x_col)
    ax.set_ylabel("Weight (mg)")
    ax.set_title(sheet_name)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    output_path = OUT_DIR / f"{sheet_name}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
