from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/06_r2/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

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
    derivative_col = next(
        (
            column
            for column in df.columns
            if "d.w" in column.lower() or "derivative" in column.lower()
        ),
        None,
    )

    if temperature_col is None or weight_col is None:
        continue

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid = temperature.notna() & weight.notna()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax1.plot(temperature[valid], weight[valid], color="tab:blue", linewidth=1.8)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.grid(True, linestyle="--", linewidth=0.6, alpha=0.65)

    if derivative_col is not None:
        derivative = pd.to_numeric(df[derivative_col], errors="coerce")
        valid_derivative = temperature.notna() & derivative.notna()
        ax2 = ax1.twinx()
        ax2.plot(
            temperature[valid_derivative],
            derivative[valid_derivative],
            color="tab:red",
            linewidth=1.5,
        )
        ax2.set_ylabel("D.W (%/°C)", color="tab:red")
        ax2.tick_params(axis="y", labelcolor="tab:red")

    ax1.set_title(sheet_name)
    fig.tight_layout()

    safe_name = "".join(
        character if character.isalnum() or character in "._- " else "_"
        for character in sheet_name
    ).strip()
    fig.savefig(out_dir / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
