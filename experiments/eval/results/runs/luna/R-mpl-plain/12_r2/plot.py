from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/12_r2/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]
    temperature_col = next(col for col in df.columns if "temperature" in col.lower())
    weight_col = next(col for col in df.columns if "weight" in col.lower())
    derivative_col = next(
        (col for col in df.columns if "d.w" in col.lower() or "dw" in col.lower()),
        None,
    )

    x = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    valid = x.notna() & weight.notna()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x[valid], weight[valid], color="tab:blue", linewidth=1.8, label="Weight (%)")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%)", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.set_title(sheet_name)
    ax.grid(True, linestyle=":", alpha=0.5)

    if derivative_col is not None:
        derivative = pd.to_numeric(df[derivative_col], errors="coerce")
        valid_derivative = x.notna() & derivative.notna()
        ax2 = ax.twinx()
        ax2.plot(
            x[valid_derivative],
            derivative[valid_derivative],
            color="tab:red",
            linewidth=1.3,
            alpha=0.8,
            label="D.W (%/°C)",
        )
        ax2.set_ylabel("D.W (%/°C)", color="tab:red")
        ax2.tick_params(axis="y", labelcolor="tab:red")

    ax.axvline(450, color="black", linestyle="--", linewidth=1.4)
    y_top = ax.get_ylim()[1]
    ax.annotate(
        "산화 시작",
        xy=(450, y_top),
        xytext=(5, -8),
        textcoords="offset points",
        rotation=90,
        ha="left",
        va="top",
        fontsize=11,
        color="black",
    )

    fig.tight_layout()
    output_name = "".join(
        char if char.isalnum() or char in "-_ " else "_" for char in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
