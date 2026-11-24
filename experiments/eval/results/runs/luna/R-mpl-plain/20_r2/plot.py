from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/20_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")

    valid = temperature.notna()
    temperature = temperature[valid]
    weight = weight[valid]
    derivative = derivative[valid]

    fig, ax_weight = plt.subplots(figsize=(9, 6))
    ax_weight.axvspan(300, 450, color="lightgray", alpha=0.55, zorder=0)

    ax_weight.plot(
        temperature, weight,
        color="tab:blue", linewidth=1.8, label="Weight(%)", zorder=2
    )
    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="tab:blue")
    ax_weight.tick_params(axis="y", labelcolor="tab:blue")
    ax_weight.set_xlim(temperature.min(), temperature.max())
    ax_weight.grid(True, alpha=0.25)

    ax_derivative = ax_weight.twinx()
    ax_derivative.plot(
        temperature, derivative,
        color="tab:red", linewidth=1.5, label="D.W(%/°C)", zorder=3
    )
    ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
    ax_derivative.tick_params(axis="y", labelcolor="tab:red")

    lines1, labels1 = ax_weight.get_legend_handles_labels()
    lines2, labels2 = ax_derivative.get_legend_handles_labels()
    ax_weight.legend(lines1 + lines2, labels1 + labels2, loc="best")

    ax_weight.set_title(f"{sheet_name} TGA")
    fig.tight_layout()

    safe_name = "".join(
        "_" if char in '<>:"/\\|?*' else char for char in sheet_name
    ).strip()
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
