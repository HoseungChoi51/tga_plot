import os
import re
import math

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import MultipleLocator

DATA_FILE = os.environ.get(
    "DATA_FILE",
    "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
)
OUT_DIR = os.environ.get(
    "OUT_DIR",
    "/home/chs/Work/tga_plot/eval/results/runs/sx_think/R-mpl-brief/02_r1/out"
)
SHEET_NAME = "1006R1-V normal"

os.makedirs(OUT_DIR, exist_ok=True)

# Korean font
font_name = "Noto Sans CJK KR"
available_fonts = {f.name for f in fm.fontManager.ttflist}
if font_name not in available_fonts:
    for f in fm.fontManager.ttflist:
        if "Noto" in f.name and "CJK" in f.name:
            font_name = f.name
            break
    else:
        font_name = "DejaVu Sans"

plt.rcParams.update({
    "font.family": font_name,
    "axes.unicode_minus": False,
})


def sanitize_filename(name: str) -> str:
    name = str(name)
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name)
    return name.strip("_")


def pick_col_index(df: pd.DataFrame, keywords, fallback: int) -> int:
    fallback = min(max(fallback, 0), len(df.columns) - 1)
    for i, col in enumerate(df.columns):
        s = str(col).lower().strip()
        if any(k in s for k in keywords):
            return i
    return fallback


def read_tga_sheet(path: str, sheet: str):
    try:
        df = pd.read_excel(path, sheet_name=sheet, header=0)
    except ValueError:
        xls = pd.ExcelFile(path)
        sheet = xls.sheet_names[0]
        df = pd.read_excel(path, sheet_name=sheet, header=0)

    # If the sheet appears to have no usable header, read without header.
    if df.shape[1] < 4:
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        df.columns = ["A", "B", "C", "D"][:df.shape[1]]

    # Excel column B -> x, C -> y1, D -> y2.
    x_idx = pick_col_index(df, ["temperature", "temp"], 1)
    y1_idx = pick_col_index(df, ["weight", "wt", "mass"], 2)
    y2_idx = pick_col_index(df, ["d.w", "dtg", "deriv", "derivative", "d wt", "dw"], 3)

    if x_idx == y1_idx:
        x_idx = 1 if len(df.columns) > 1 else x_idx
    if y1_idx == y2_idx:
        y2_idx = 3 if len(df.columns) > 3 else y2_idx

    x = pd.to_numeric(df.iloc[:, x_idx], errors="coerce")
    y1 = pd.to_numeric(df.iloc[:, y1_idx], errors="coerce")
    y2 = pd.to_numeric(df.iloc[:, y2_idx], errors="coerce")

    mask = x.notna() & y1.notna() & y2.notna()
    x = x[mask].to_numpy(dtype=float)
    y1 = y1[mask].to_numpy(dtype=float)
    y2 = y2[mask].to_numpy(dtype=float)

    return sheet, x, y1, y2


def main():
    sheet, x, y1, y2 = read_tga_sheet(DATA_FILE, SHEET_NAME)
    out_path = os.path.join(OUT_DIR, f"{sanitize_filename(sheet)}.png")

    if len(x) == 0:
        fig, ax = plt.subplots(figsize=(8.5, 6.0))
        ax.text(0.5, 0.5, "No usable data", ha="center", va="center")
        ax.set_title(sheet)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return

    # DTG is multiplied by -1 so that mass-loss peaks point upward.
    y2_plot = -y2

    fig, ax1 = plt.subplots(figsize=(8.5, 6.0))
    ax2 = ax1.twinx()

    line1, = ax1.plot(
        x, y1,
        color="#1f4e9c",
        linewidth=1.8,
        label="Weight (%)"
    )
    line2, = ax2.plot(
        x, y2_plot,
        color="#c0392b",
        linewidth=1.8,
        label="Deriv. Weight (−%/°C)"
    )

    # Tick spacing
    x_step = 200.0
    y1_step = 20.0
    y2_step = 0.2

    # Axis limits
    x_max = float(np.nanmax(x))
    x_limit = max(x_step, float(math.ceil(x_max / x_step - 1e-12) * x_step))

    y1_max = float(np.nanmax(y1))
    y1_limit = max(y1_step, float(math.ceil(y1_max / y1_step - 1e-12) * y1_step))

    y2_min_raw = float(np.nanmin(y2_plot))
    y2_max_raw = float(np.nanmax(y2_plot))

    y2_min = min(
        0.0,
        float(math.floor(y2_min_raw / y2_step + 1e-12) * y2_step)
    )
    y2_limit = max(
        y2_step,
        float(math.ceil(y2_max_raw / y2_step - 1e-12) * y2_step)
    )

    ax1.set_xlim(0.0, x_limit)
    ax1.set_ylim(0.0, y1_limit)
    ax2.set_ylim(y2_min, y2_limit)

    ax1.xaxis.set_major_locator(MultipleLocator(x_step))
    ax1.yaxis.set_major_locator(MultipleLocator(y1_step))
    ax2.yaxis.set_major_locator(MultipleLocator(y2_step))

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("Deriv. Weight (−%/°C)")
    ax1.set_title(sheet)

    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    # Residue: weight at the measured temperature closest to 800 °C
    res_idx = int(np.argmin(np.abs(x - 800.0)))
    res_temp = float(x[res_idx])
    res_weight = float(y1[res_idx])

    ax1.plot(
        res_temp, res_weight,
        "o",
        color="#1f4e9c",
        markersize=7,
        zorder=5
    )

    if res_weight < y1_limit * 0.25:
        res_offset = (10, 12)
        res_va = "bottom"
    else:
        res_offset = (10, -12)
        res_va = "top"

    ax1.annotate(
        f"Residue {res_weight:.1f}%",
        xy=(res_temp, res_weight),
        xytext=res_offset,
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=10,
        fontweight="bold",
        ha="left",
        va=res_va,
        bbox=dict(
            boxstyle="round,pad=0.25",
            fc="white",
            ec="#1f4e9c",
            alpha=0.85
        ),
        zorder=6
    )

    # DTG peak: highest inverted DTG value above 150 °C.
    peak_mask = x > 150.0
    if np.any(peak_mask):
        peak_indices = np.where(peak_mask)[0]
        peak_idx = int(peak_indices[np.argmax(y2_plot[peak_indices])])
    else:
        peak_idx = int(np.argmax(y2_plot))

    peak_temp = float(x[peak_idx])
    peak_val = float(y2_plot[peak_idx])

    ax2.plot(
        peak_temp, peak_val,
        "o",
        color="#c0392b",
        markersize=7,
        zorder=5
    )

    if peak_val > y2_limit * 0.75:
        peak_offset = (10, -12)
        peak_va = "top"
    else:
        peak_offset = (10, 12)
        peak_va = "bottom"

    ax2.annotate(
        f"Peak {peak_temp:.0f} °C\nmax {peak_val:.2f}",
        xy=(peak_temp, peak_val),
        xytext=peak_offset,
        textcoords="offset points",
        color="#c0392b",
        fontsize=10,
        fontweight="bold",
        ha="left",
        va=peak_va,
        bbox=dict(
            boxstyle="round,pad=0.25",
            fc="white",
            ec="#c0392b",
            alpha=0.85
        ),
        zorder=6
    )

    ax1.legend(
        [line1, line2],
        [line1.get_label(), line2.get_label()],
        loc="center left",
        framealpha=0.9
    )

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
