from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/18_r3/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    required = ["Temperature", "Weight(%)", "D.W(%/C)"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{sheet_name!r} 시트에 필요한 열이 없습니다: {missing}")

    data = df[required].apply(pd.to_numeric, errors="coerce").dropna()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        data["Temperature"],
        data["Weight(%)"],
        color="tab:blue",
        linewidth=1.8,
        label="Weight(%)",
    )
    line2, = ax2.plot(
        data["Temperature"],
        data["D.W(%/C)"],
        color="tab:red",
        linewidth=1.5,
        label="D.W(%/C)",
    )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="tab:blue")
    ax2.set_ylabel("D.W (%/°C)", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    ax1.xaxis.set_major_locator(MultipleLocator(100))
    ax2.set_ylim(-0.05, 1.2)

    ax1.set_title(sheet_name)
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="best")

    fig.tight_layout()
    output_name = "".join(
        char if char.isalnum() or char in "-_." else "_" for char in sheet_name
    )
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
