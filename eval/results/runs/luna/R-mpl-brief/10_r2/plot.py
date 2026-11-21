from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/10_r2/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def safe_filename(name):
    return "".join("_" if char in '<>:"/\\|?*' else char for char in str(name)).strip()


def find_column(columns, terms):
    lowered = {str(column).strip().lower(): column for column in columns}
    for term in terms:
        for lowered_name, original in lowered.items():
            if term in lowered_name:
                return original
    return None


def plot_sheet(sheet_name, data):
    data = data.dropna(how="all")
    x_col = find_column(data.columns, ["temperature", "temp"])
    weight_col = find_column(data.columns, ["weight", "mass"])
    dtg_col = find_column(data.columns, ["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        raise ValueError(f"필요한 온도/무게/DTG 열을 찾을 수 없습니다: {sheet_name}")

    x = pd.to_numeric(data[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(data[weight_col], errors="coerce").to_numpy()
    dtg = pd.to_numeric(data[dtg_col], errors="coerce").to_numpy()
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if not len(x):
        raise ValueError(f"유효한 데이터가 없습니다: {sheet_name}")

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(x, weight, color="#1f4e9c", label="Weight (%)")
    dtg_line, = ax2.plot(x, -dtg, color="#c0392b", label="DTG")

    residue_index = int(np.argmin(np.abs(x - 700)))
    residue_temp = x[residue_index]
    residue_value = weight[residue_index]
    ax1.plot(residue_temp, residue_value, "o", color="#1f4e9c", markersize=6)
    ax1.annotate(
        f"Residue {residue_value:.2f}%",
        (residue_temp, residue_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_index = peak_candidates[np.argmax((-dtg)[peak_candidates])]
        peak_temp = x[peak_index]
        peak_value = -dtg[peak_index]
        ax2.plot(peak_temp, peak_value, "o", color="#c0392b", markersize=6)
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            (peak_temp, peak_value),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (%/°C)")
    ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG"], loc="center left")
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()

    output_path = OUT_DIR / f"{safe_filename(sheet_name)}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheets = pd.read_excel(DATA_FILE, sheet_name=None)
    for sheet_name, data in sheets.items():
        plot_sheet(sheet_name, data)


if __name__ == "__main__":
    main()
