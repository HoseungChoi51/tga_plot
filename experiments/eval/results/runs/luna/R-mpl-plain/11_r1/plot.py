from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/11_r1/out"

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    sheets = pd.read_excel(DATA_FILE, sheet_name=None)
    fig, (ax_weight, ax_derivative) = plt.subplots(
        2, 1, figsize=(10, 8), sharex=True, constrained_layout=True
    )

    colors = ["#1f77b4", "#d62728", "#2ca02c"]

    for (sheet_name, df), color in zip(sheets.items(), colors):
        df.columns = [str(column).strip() for column in df.columns]
        required = {"Temperature", "Weight(%)", "D.W(%/C)"}
        if not required.issubset(df.columns):
            continue

        data = df[["Temperature", "Weight(%)", "D.W(%/C)"]].apply(
            pd.to_numeric, errors="coerce"
        ).dropna()

        ax_weight.plot(
            data["Temperature"], data["Weight(%)"],
            color=color, linewidth=1.8, label=sheet_name
        )
        ax_derivative.plot(
            data["Temperature"], data["D.W(%/C)"],
            color=color, linewidth=1.8, label=sheet_name
        )

    ax_weight.set_ylabel("Weight (%)")
    ax_weight.set_title("TGA")
    ax_weight.grid(True, alpha=0.3)
    ax_weight.legend(frameon=False)

    ax_derivative.set_xlabel("Temperature (°C)")
    ax_derivative.set_ylabel("D.W (%/°C)")
    ax_derivative.grid(True, alpha=0.3)
    ax_derivative.legend(frameon=False)

    # 피크 마커 및 피크 라벨은 표시하지 않습니다.
    output_path = out_dir / "TGA_no_peaks.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
