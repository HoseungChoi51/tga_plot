from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/13_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

excel = pd.ExcelFile(DATA_FILE)
for sheet_name in excel.sheet_names:
    df = pd.read_excel(excel, sheet_name=sheet_name)
    df.columns = [str(col).strip() for col in df.columns]

    x_col = "Temperature (°C)"
    y_col = "Weight (mg)"
    if x_col not in df.columns or y_col not in df.columns:
        continue

    data = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(data[x_col], data[y_col], color="tab:blue", linewidth=1.8)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (mg)")
    ax.set_title(sheet_name)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(sheet_name))
    fig.savefig(out_dir / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
