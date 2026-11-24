from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/20_r3/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(excel, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

    valid = temperature.notna()
    temperature = temperature[valid]
    weight = weight[valid]
    derivative = derivative[valid]

    fig, ax_weight = plt.subplots(figsize=(9, 5.5))
    ax_derivative = ax_weight.twinx()

    ax_weight.axvspan(300, 450, color="lightgray", alpha=0.55, zorder=0)
    ax_weight.plot(temperature, weight, color="tab:blue", linewidth=1.8, label="Weight")
    ax_derivative.plot(
        temperature, derivative, color="tab:red", linewidth=1.5, label="Derivative weight"
    )

    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="tab:blue")
    ax_derivative.set_ylabel("D.W. (%/°C)", color="tab:red")
    ax_weight.tick_params(axis="y", labelcolor="tab:blue")
    ax_derivative.tick_params(axis="y", labelcolor="tab:red")
    ax_weight.set_title(sheet_name)
    ax_weight.grid(True, alpha=0.25)

    fig.tight_layout()
    safe_name = "".join(
        character if character.isalnum() or character in "-_." else "_"
        for character in sheet_name
    )
    fig.savefig(out_dir / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
