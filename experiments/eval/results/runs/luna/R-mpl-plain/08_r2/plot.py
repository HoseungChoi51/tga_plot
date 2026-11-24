from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/08_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    # Expected columns: Temperature, Weight(%), D.W(%/C)
    df.columns = [str(column).strip() for column in df.columns]
    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

    valid = temperature.notna() & weight.notna() & derivative.notna()
    fig, ax1 = plt.subplots(figsize=(9, 6))

    line1 = ax1.plot(
        temperature[valid],
        weight[valid],
        color="tab:blue",
        linewidth=1.8,
        label="무게",
    )
    ax1.set_xlabel("온도 (°C)")
    ax1.set_ylabel("무게 (%)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(True, linestyle="--", alpha=0.35)

    ax2 = ax1.twinx()
    line2 = ax2.plot(
        temperature[valid],
        derivative[valid],
        color="tab:red",
        linewidth=1.5,
        label="미분 무게",
    )
    ax2.set_ylabel("미분 무게 (%/°C)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    ax1.set_title(sheet_name)
    lines = line1 + line2
    ax1.legend(lines, [line.get_label() for line in lines], loc="best")

    fig.tight_layout()
    output_name = "".join(
        char if char.isalnum() or char in "-_ " else "_" for char in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
