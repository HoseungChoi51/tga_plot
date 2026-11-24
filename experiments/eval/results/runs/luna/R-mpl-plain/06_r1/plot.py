from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/06_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    required = {"Temperature", "Weight(%)", "D.W(%/C)"}
    if not required.issubset(df.columns):
        continue

    data = df[["Temperature", "Weight(%)", "D.W(%/C)"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()

    fig, ax_weight = plt.subplots(figsize=(9, 6))
    ax_derivative = ax_weight.twinx()

    ax_weight.plot(data["Temperature"], data["Weight(%)"], color="tab:blue", linewidth=1.8)
    ax_derivative.plot(data["Temperature"], data["D.W(%/C)"], color="tab:red", linewidth=1.5)

    ax_weight.set_xlabel("Temperature (°C)")
    ax_weight.set_ylabel("Weight (%)", color="tab:blue")
    ax_derivative.set_ylabel("D.W (%/°C)", color="tab:red")
    ax_weight.tick_params(axis="y", labelcolor="tab:blue")
    ax_derivative.tick_params(axis="y", labelcolor="tab:red")
    ax_weight.set_title(sheet_name)

    ax_weight.grid(True, linestyle="--", linewidth=0.6, alpha=0.7)
    # 범례는 표시하지 않습니다.
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in sheet_name).strip()
    fig.savefig(out_dir / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
