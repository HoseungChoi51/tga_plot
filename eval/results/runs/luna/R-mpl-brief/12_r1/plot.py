from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/12_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def safe_filename(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in str(name))


def find_column(columns, keyword, fallback_index):
    for col in columns:
        if keyword.lower() in str(col).lower():
            return col
    return columns[fallback_index]


OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    if df.empty or len(df.columns) < 4:
        continue

    x_col = find_column(df.columns, "temperature", 1)
    weight_col = find_column(df.columns, "weight", 2)
    dtg_col = next(
        (col for col in df.columns if "dtg" in str(col).lower() or "d.w" in str(col).lower()),
        df.columns[3],
    )

    x = pd.to_numeric(df[x_col], errors="coerce").to_numpy()
    weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
    dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()
    valid = np.isfinite(x) & np.isfinite(weight) & np.isfinite(dtg)
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if not len(x):
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(x, -dtg, color="#c0392b", linewidth=1.5, label="DTG")

    # Residue at the measured point nearest 800 °C.
    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.plot(x[residue_idx], weight[residue_idx], "o", color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(7, 9),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward-pointing DTG peak above 150 °C.
    peak_candidates = np.flatnonzero(x > 150)
    if len(peak_candidates):
        peak_idx = peak_candidates[np.argmax(-dtg[peak_candidates])]
        ax2.plot(x[peak_idx], -dtg[peak_idx], "o", color="#c0392b", zorder=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], -dtg[peak_idx]),
            xytext=(7, 9),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    # Oxidation-start reference line.
    ax1.axvline(450, color="#555555", linestyle="--", linewidth=1.2)
    ax1.text(
        450,
        0.98,
        "산화 시작",
        transform=ax1.get_xaxis_transform(),
        rotation=90,
        va="top",
        ha="right",
        color="#444444",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 2},
    )

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.25)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
