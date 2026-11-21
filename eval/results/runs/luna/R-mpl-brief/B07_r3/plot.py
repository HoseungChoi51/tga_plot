from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B07_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def find_column(columns, keywords):
    """Return the first column whose name contains any of the supplied keywords."""
    for keyword in keywords:
        for col in columns:
            if keyword in str(col).lower():
                return col
    return None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # The requested second sheet is PVC.
    df = pd.read_excel(DATA_FILE, sheet_name=1)
    x_col = find_column(df.columns, ("temperature", "temp"))
    weight_col = find_column(df.columns, ("weight", "mass"))

    if x_col is None or weight_col is None:
        raise ValueError(f"Temperature or weight column not found. Columns: {list(df.columns)}")

    data = df[[x_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
    data = data.sort_values(x_col)
    temperature = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight")

    for target in (300, 600):
        idx = int(np.argmin(np.abs(temperature - target)))
        measured_temp = temperature[idx]
        measured_weight = weight[idx]
        ax.scatter(
            measured_temp,
            measured_weight,
            color="#d35400",
            edgecolor="white",
            linewidth=0.8,
            s=65,
            zorder=4,
        )
        ax.annotate(
            f"{target} °C: {measured_weight:.2f}%",
            xy=(measured_temp, measured_weight),
            xytext=(8, 10 if target == 300 else -20),
            textcoords="offset points",
            color="#333333",
            fontsize=10,
            arrowprops={"arrowstyle": "-", "color": "#777777", "lw": 0.8},
        )

    ax.set_title("PVC")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Weight (%)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    fig.savefig(OUT_DIR / "PVC_weight_at_300_600C.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
