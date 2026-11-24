from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/09_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_column(columns, keywords):
    for col in columns:
        name = str(col).strip().lower()
        if any(keyword in name for keyword in keywords):
            return col
    return None


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    x_col = find_column(df.columns, ("temperature", "temp"))
    weight_col = find_column(df.columns, ("weight", "mass"))
    dtg_col = find_column(df.columns, ("d.w", "dtg", "derivative"))

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    x = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg_up = -data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", label="Weight")
    ax2.plot(x, dtg_up, color="#c0392b", label="DTG")

    residue_idx = int(np.argmin(np.abs(x - 800)))
    ax1.scatter(x[residue_idx], weight[residue_idx], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {weight[residue_idx]:.1f}%",
        (x[residue_idx], weight[residue_idx]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    peak_mask = x > 150
    if peak_mask.any():
        peak_candidates = np.flatnonzero(peak_mask)
        peak_idx = peak_candidates[np.argmax(dtg_up[peak_mask])]
        ax2.scatter(x[peak_idx], dtg_up[peak_idx], color="#c0392b", zorder=5)
        ax2.annotate(
            f"{x[peak_idx]:.0f} °C",
            (x[peak_idx], dtg_up[peak_idx]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
    ax1.set_title(str(sheet_name))

    ax1.tick_params(axis="both", direction="out", labelsize=9)
    ax2.tick_params(axis="y", direction="out", labelsize=9)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(sheet_name)).strip()
    fig.savefig(OUT_DIR / f"{safe_name or 'plot'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
