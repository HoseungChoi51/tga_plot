from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/08_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

    valid = temperature.notna() & weight.notna() & derivative.notna()
    temperature = temperature[valid]
    weight = weight[valid]
    derivative = derivative[valid]

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        temperature, weight, color="tab:blue", linewidth=1.8, label="Weight"
    )
    line2, = ax2.plot(
        temperature, derivative, color="tab:red", linewidth=1.5, label="Derivative"
    )

    ax1.set_xlabel("온도 (°C)")
    ax1.set_ylabel("무게 (%)", color="tab:blue")
    ax2.set_ylabel("미분 무게 (%/°C)", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:red")
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.set_title(sheet_name)

    ax1.legend(
        [line1, line2],
        ["무게 (%)", "미분 무게 (%/°C)"],
        loc="best",
        frameon=False,
    )

    fig.tight_layout()
    output_name = "".join(
        character if character.isalnum() or character in "-_ " else "_"
        for character in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
