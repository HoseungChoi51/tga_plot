from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/09_r2/out")

# Korean-capable font configuration
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, data in sheets.items():
    data.columns = [str(column).strip() for column in data.columns]

    temperature_col = next(
        (column for column in data.columns if "temperature" in column.lower()),
        None,
    )
    weight_col = next(
        (column for column in data.columns if "weight" in column.lower()),
        None,
    )
    derivative_col = next(
        (
            column
            for column in data.columns
            if "d.w" in column.lower() or "derivative" in column.lower()
        ),
        None,
    )

    if temperature_col is None or weight_col is None:
        continue

    temperature = pd.to_numeric(data[temperature_col], errors="coerce")
    weight = pd.to_numeric(data[weight_col], errors="coerce")

    fig, ax_weight = plt.subplots(figsize=(8, 5))
    ax_weight.plot(temperature, weight, color="tab:blue", linewidth=1.8)
    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="tab:blue")
    ax_weight.tick_params(axis="y", labelcolor="tab:blue")
    ax_weight.set_title(sheet_name)
    ax_weight.grid(True, alpha=0.25)

    if derivative_col is not None:
        derivative = pd.to_numeric(data[derivative_col], errors="coerce")
        ax_derivative = ax_weight.twinx()
        ax_derivative.plot(
            temperature,
            derivative,
            color="tab:red",
            linewidth=1.5,
        )
        ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
        ax_derivative.tick_params(axis="y", labelcolor="tab:red")

    for ax in fig.axes:
        ax.tick_params(axis="both", direction="out", labelsize=9)

    fig.tight_layout()
    output_name = "".join(
        character if character.isalnum() or character in "-_ " else "_"
        for character in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
