from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/07_r2/out"

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    sheets = pd.read_excel(DATA_FILE, sheet_name=None)

    for sheet_name, df in sheets.items():
        df.columns = [str(col).strip() for col in df.columns]

        temperature_col = next((c for c in df.columns if "temperature" in c.lower()), None)
        weight_col = next((c for c in df.columns if "weight" in c.lower()), None)
        derivative_col = next(
            (c for c in df.columns if "d.w" in c.lower() or "dw(" in c.lower()),
            None,
        )

        if temperature_col is None or weight_col is None:
            continue

        x = pd.to_numeric(df[temperature_col], errors="coerce")
        weight = pd.to_numeric(df[weight_col], errors="coerce")

        fig, ax = plt.subplots(figsize=(9, 6))
        ax.plot(x, weight, color="tab:blue", linewidth=1.8, label="Weight (%)")
        ax.set_xlabel("Temperature (°C)")
        ax.set_ylabel("Weight (%)")
        ax.set_title(sheet_name)
        ax.grid(True, alpha=0.3)

        if derivative_col is not None:
            derivative = pd.to_numeric(df[derivative_col], errors="coerce")
            ax2 = ax.twinx()
            ax2.plot(
                x,
                derivative,
                color="tab:red",
                linewidth=1.4,
                label="D.W (%/°C)",
            )
            ax2.set_ylabel("D.W (%/°C)")

            lines = ax.get_lines() + ax2.get_lines()
            labels = [line.get_label() for line in lines]
            ax.legend(lines, labels, loc="upper right", fontsize=9)
        else:
            ax.legend(loc="upper right", fontsize=9)

        fig.tight_layout()
        safe_name = "".join(
            ch if ch.isalnum() or ch in "-_ " else "_" for ch in str(sheet_name)
        ).strip().replace(" ", "_")
        fig.savefig(out_dir / f"{safe_name}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

if __name__ == "__main__":
    main()
