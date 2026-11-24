from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B15_r1/out")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    plt.rcParams["font.family"] = "Noto Sans CJK KR"
    plt.rcParams["axes.unicode_minus"] = False

    excel = pd.ExcelFile(DATA_FILE)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    for sheet_name in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet_name)
        df.columns = [str(column).strip() for column in df.columns]

        temperature_col = next(
            (column for column in df.columns if "Temperature" in column),
            None,
        )
        weight_col = next(
            (column for column in df.columns if "Weight" in column and "Deriv" not in column),
            None,
        )
        if temperature_col is None or weight_col is None:
            raise ValueError(f"{sheet_name} 시트에서 온도 또는 중량 열을 찾을 수 없습니다.")

        data = df[[temperature_col, weight_col]].apply(pd.to_numeric, errors="coerce").dropna()
        ax.plot(data[temperature_col], data[weight_col], linewidth=1.8, label=sheet_name)

    ax.set_xlabel("온도 (°C)")
    ax.set_ylabel("중량 (%)")
    ax.set_title("고분자 시료의 TGA 곡선")
    ax.grid(True, alpha=0.3)
    ax.legend(title="시료", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "polymers_tga_overlay.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
