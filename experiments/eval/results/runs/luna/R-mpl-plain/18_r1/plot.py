from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/18_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = ["1006R1-V normal", "1006R1-V acid", "1006R1-V 750C"]

for sheet_name in sheets:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(column).strip() for column in df.columns]

    temperature = pd.to_numeric(df["Temperature"], errors="coerce")
    weight = pd.to_numeric(df["Weight(%)"], errors="coerce")
    derivative = pd.to_numeric(df["D.W(%/C)"], errors="coerce")
    valid = temperature.notna() & weight.notna() & derivative.notna()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(temperature[valid], weight[valid], color="tab:blue", linewidth=1.8,
             label="Weight(%)")
    ax2.plot(temperature[valid], derivative[valid], color="tab:red", linewidth=1.5,
             label="D.W(%/C)")

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="tab:blue")
    ax2.set_ylabel("D.W (%/°C)", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    xmin = temperature[valid].min()
    xmax = temperature[valid].max()
    tick_start = (int(xmin) // 100) * 100
    ax1.set_xticks(range(tick_start, int(xmax) + 1, 100))
    ax2.set_ylim(-0.05, 1.2)

    ax1.set_title(sheet_name)
    ax1.grid(True, axis="both", linestyle="--", alpha=0.35)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", frameon=False)

    fig.tight_layout()
    safe_name = sheet_name.replace("/", "-")
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
