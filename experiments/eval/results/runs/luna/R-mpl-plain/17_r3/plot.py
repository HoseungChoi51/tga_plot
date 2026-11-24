from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/17_r3/out"

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    sheets = pd.read_excel(DATA_FILE, sheet_name=None)
    for sheet_name, df in sheets.items():
        df.columns = [str(col).strip() for col in df.columns]
        required = ["Temperature", "Weight(%)", "D.W(%/C)"]
        if not all(col in df.columns for col in required):
            continue

        data = df[required].apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        fig, ax1 = plt.subplots(figsize=(8, 5))
        ax2 = ax1.twinx()

        ax1.plot(
            data["Temperature"], data["Weight(%)"],
            color="tab:blue", linewidth=1.8, label="Weight (%)"
        )
        ax2.plot(
            data["Temperature"], data["D.W(%/C)"],
            color="tab:red", linewidth=1.5, label="D.W. (%/°C)"
        )

        ax1.set_xlabel("Temperature (°C)")
        ax1.set_ylabel("Weight (%)", color="tab:blue")
        ax2.set_ylabel("D.W. (%/°C)", color="tab:red")
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax2.tick_params(axis="y", labelcolor="tab:red")
        ax1.set_title(sheet_name)
        ax1.grid(True, linestyle="--", alpha=0.35)

        lines = ax1.get_lines() + ax2.get_lines()
        ax1.legend(lines, [line.get_label() for line in lines], loc="best")
        fig.tight_layout()

        safe_name = "".join(
            "_" if char in '<>:"/\\|?*' else char for char in sheet_name
        ).strip()
        fig.savefig(out_dir / f"{safe_name or 'TGA'}.png", dpi=600, bbox_inches="tight")
        plt.close(fig)

if __name__ == "__main__":
    main()
