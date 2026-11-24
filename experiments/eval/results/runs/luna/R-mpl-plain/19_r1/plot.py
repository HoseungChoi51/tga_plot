from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/19_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean-capable font and consistent gray text at 13 pt.
plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": 13,
    "text.color": "gray",
    "axes.labelcolor": "gray",
    "axes.titlecolor": "gray",
    "xtick.color": "gray",
    "ytick.color": "gray",
    "legend.labelcolor": "gray",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(
        (c for c in df.columns if "temperature" in c.lower()), None
    )
    weight_col = next(
        (c for c in df.columns if "weight" in c.lower()), None
    )
    derivative_col = next(
        (c for c in df.columns if "d.w" in c.lower() or "dw" in c.lower()), None
    )

    if temperature_col is None or weight_col is None:
        continue

    plot_cols = [temperature_col, weight_col]
    if derivative_col is not None:
        plot_cols.append(derivative_col)
    data = df[plot_cols].apply(pd.to_numeric, errors="coerce").dropna(
        subset=[temperature_col, weight_col]
    )

    fig, ax_weight = plt.subplots(figsize=(9, 6))
    ax_weight.plot(
        data[temperature_col],
        data[weight_col],
        color="#2878B5",
        linewidth=2,
        label=weight_col,
    )
    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)")
    ax_weight.set_title(sheet_name)
    ax_weight.grid(True, linestyle="--", alpha=0.3)

    if derivative_col is not None:
        derivative_data = data.dropna(subset=[derivative_col])
        ax_derivative = ax_weight.twinx()
        ax_derivative.plot(
            derivative_data[temperature_col],
            derivative_data[derivative_col],
            color="#D9534F",
            linewidth=1.8,
            label=derivative_col,
        )
        ax_derivative.set_ylabel("D.W (%/°C)", color="gray")
        ax_derivative.tick_params(axis="y", colors="gray")

        lines1, labels1 = ax_weight.get_legend_handles_labels()
        lines2, labels2 = ax_derivative.get_legend_handles_labels()
        ax_weight.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc="best",
            frameon=False,
        )
    else:
        ax_weight.legend(loc="best", frameon=False)

    for spine in ax_weight.spines.values():
        spine.set_color("gray")
    if derivative_col is not None:
        for spine in ax_derivative.spines.values():
            spine.set_color("gray")

    fig.tight_layout()
    safe_name = "".join(
        char if char.isalnum() or char in "-_ " else "_"
        for char in sheet_name
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
