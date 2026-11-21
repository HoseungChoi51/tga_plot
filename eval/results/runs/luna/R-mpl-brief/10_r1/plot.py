from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/10_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

def find_column(columns, keywords):
    for col in columns:
        name = str(col).strip().lower()
        if any(keyword in name for keyword in keywords):
            return col
    return None

def safe_filename(name):
    return "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(name)).strip().replace(" ", "_")

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    x_col = find_column(df.columns, ["temperature", "temp"])
    weight_col = find_column(df.columns, ["weight", "mass"])
    dtg_col = find_column(df.columns, ["d.w", "dtg", "derivative", "deriv"])

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    x = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg = data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(8, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(x, -dtg, color="#c0392b", linewidth=1.5, label="DTG")

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.3)

    # Residue: measured weight at the point nearest 700 °C.
    residue_idx = int(np.argmin(np.abs(x - 700)))
    residue_temp = x[residue_idx]
    residue_weight = weight[residue_idx]
    ax1.scatter([residue_temp], [residue_weight], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {residue_weight:.2f}%",
        xy=(residue_temp, residue_weight),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward DTG peak above 150 °C.
    peak_candidates = np.flatnonzero(x > 150)
    if peak_candidates.size:
        peak_idx = peak_candidates[np.argmax((-dtg)[peak_candidates])]
        peak_temp = x[peak_idx]
        peak_value = -dtg[peak_idx]
        ax2.scatter([peak_temp], [peak_value], color="#c0392b", zorder=5)
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            xy=(peak_temp, peak_value),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
