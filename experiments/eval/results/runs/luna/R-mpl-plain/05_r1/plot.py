from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/05_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# 각 시트의 Temperature를 x축, Weight(%)를 y1, D.W(%/C)를 y2로 표시합니다.
excel = pd.ExcelFile(DATA_FILE)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    df.columns = [str(col).strip() for col in df.columns]

    required = ["Temperature", "Weight(%)", "D.W(%/C)"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"시트 '{sheet_name}'에 필요한 열이 없습니다: {missing}")

    data = df[required].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(
        data["Temperature"],
        data["Weight(%)"],
        color="black",
        linewidth=2.5,
        label="Weight(%)",
    )
    ax2.plot(
        data["Temperature"],
        data["D.W(%/C)"],
        linestyle="--",
        label="D.W(%/C)",
    )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("D.W (%/°C)")
    ax1.set_title(sheet_name)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

    ax1.grid(True, alpha=0.25)
    fig.tight_layout()

    output_name = "".join(
        "_" if char in '<>:"/\\|?*' else char for char in sheet_name
    )
    fig.savefig(OUT_DIR / f"{output_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
