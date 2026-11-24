import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx_think/R-mpl-brief/B21_r1/out"


def setup_font():
    preferred = "Noto Sans CJK KR"
    try:
        available = {f.name for f in font_manager.fontManager.ttflist}
    except Exception:
        available = set()

    if preferred not in available:
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKKR-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    font_manager.fontManager.addfont(path)
                    available.add(preferred)
                    break
                except Exception:
                    pass

    if preferred in available:
        plt.rcParams["font.family"] = [preferred, "sans-serif"]
    else:
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = [preferred, "DejaVu Sans"]

    plt.rcParams["axes.unicode_minus"] = False


def find_column(df, keywords, exclude=()):
    for col in df.columns:
        name = str(col).lower()
        if any(k in name for k in keywords):
            if not any(e in name for e in exclude):
                return col
    return None


def sanitize_filename(name):
    name = re.sub(r'[^\w\-\.\s]+', "_", str(name)).strip()
    return name if name else "plot"


def plot_tga_sheet(df, sheet_name, out_path):
    df = df.copy()

    temp_col = find_column(df, ["temperature", "temp", "온도"])
    weight_col = find_column(df, ["weight", "wt", "무게", "질량"], exclude=["deriv", "dtg", "derivative", "d/dt"])
    dtg_col = find_column(df, ["deriv", "dtg", "derivative", "d/dt", "미분"])

    if temp_col is None:
        temp_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    if weight_col is None:
        weight_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]
    if dtg_col is None:
        dtg_col = df.columns[3] if len(df.columns) > 3 else df.columns[-1]

    if len({temp_col, weight_col, dtg_col}) < 3 and len(df.columns) >= 4:
        temp_col, weight_col, dtg_col = df.columns[1], df.columns[2], df.columns[3]

    temp = pd.to_numeric(df[temp_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg_raw = pd.to_numeric(df[dtg_col], errors="coerce")

    mask = np.isfinite(temp) & np.isfinite(weight) & np.isfinite(dtg_raw)
    temp = temp[mask].to_numpy(dtype=float)
    weight = weight[mask].to_numpy(dtype=float)
    dtg_raw = dtg_raw[mask].to_numpy(dtype=float)

    if temp.size == 0:
        return

    order = np.argsort(temp, kind="mergesort")
    temp = temp[order]
    weight = weight[order]
    dtg_raw = dtg_raw[order]

    dtg_plot = -dtg_raw

    fig, ax1 = plt.subplots(figsize=(7.5, 5.0))

    line1, = ax1.plot(
        temp,
        weight,
        color="#1f4e9c",
        linewidth=1.8,
        label="Weight (%)",
    )
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")

    ax2 = ax1.twinx()
    line2, = ax2.plot(
        temp,
        dtg_plot,
        color="#c0392b",
        linewidth=1.8,
        label="DTG (%/°C) (×-1)",
    )
    ax2.set_ylabel("DTG (%/°C) (×-1)")

    ax1.set_title(sheet_name)

    idx_res = int(np.argmin(np.abs(temp - 800.0)))
    residue = float(weight[idx_res])
    ax1.plot(
        temp[idx_res],
        residue,
        marker="o",
        color="#1f4e9c",
        markersize=6,
        linestyle="None",
        zorder=5,
    )
    ax1.annotate(
        f"Residue {residue:.1f}%",
        xy=(temp[idx_res], residue),
        xytext=(10, -15),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=10,
        ha="left",
        va="top",
        zorder=6,
    )

    peak_mask = temp > 150.0
    if np.any(peak_mask):
        peak_indices = np.flatnonzero(peak_mask)
        idx_peak = peak_indices[int(np.argmax(dtg_plot[peak_indices]))]
        peak_temp = float(temp[idx_peak])
        peak_dtg = float(dtg_plot[idx_peak])

        ax2.plot(
            peak_temp,
            peak_dtg,
            marker="o",
            color="#c0392b",
            markersize=6,
            linestyle="None",
            zorder=5,
        )
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            xy=(peak_temp, peak_dtg),
            xytext=(0, 10),
            textcoords="offset points",
            color="#c0392b",
            fontsize=10,
            ha="center",
            va="bottom",
            zorder=6,
        )

    ax1.legend(
        [line1, line2],
        [line1.get_label(), line2.get_label()],
        loc="center left",
        framealpha=0.9,
    )

    x_min = float(np.nanmin(temp))
    x_max = float(np.nanmax(temp))
    if np.isfinite(x_min) and np.isfinite(x_max) and x_max > x_min:
        ax1.set_xlim(x_max, x_min)
        ax2.set_xlim(x_max, x_min)
    else:
        ax1.invert_xaxis()
        ax2.invert_xaxis()

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def main():
    setup_font()
    os.makedirs(OUT_DIR, exist_ok=True)

    try:
        df = pd.read_excel(DATA_FILE, sheet_name="Raw", header=0)
    except Exception:
        df = pd.read_excel(DATA_FILE, sheet_name=0, header=0)

    out_path = os.path.join(OUT_DIR, sanitize_filename("Raw") + ".png")
    plot_tga_sheet(df, "Raw", out_path)


if __name__ == "__main__":
    main()
