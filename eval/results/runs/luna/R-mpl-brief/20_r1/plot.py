from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/20_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

def find_column(columns, candidates):
    lowered = {str(col).strip().lower(): col for col in columns}
    for candidate in candidates:
        for key, original in lowered.items():
            if candidate in key:
                return original
    return None

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    x_col = find_column(df.columns, ["temperature", "temp"])
    weight_col = find_column(df.columns, ["weight"])
    dtg_col = find_column(df.columns, ["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        continue

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()
    x, weight, dtg = x[valid], weight[valid], dtg[valid]
    if x.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax1.axvspan(300, 450, color="lightgray", alpha=0.55, zorder=0)
    weight_line, = ax1.plot(x, weight, color="#1f4e9c", label="Weight (%)", zorder=2)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")

    ax2 = ax1.twinx()
    dtg_up = -dtg
    dtg_line, = ax2.plot(x, dtg_up, color="#c0392b", label="-DTG (%/°C)", zorder=2)
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    # Residue at the measured point nearest 800 °C.
    residue_idx = (x - 800).abs().idxmin()
    residue_x = float(x.loc[residue_idx])
    residue_y = float(weight.loc[residue_idx])
    ax1.scatter([residue_x], [residue_y], color="#1f4e9c", edgecolor="white", zorder=5)
    ax1.annotate(
        f"Residue {residue_y:.1f}%",
        xy=(residue_x, residue_y),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward DTG peak above 150 °C.
    peak_candidates = (x > 150) & dtg_up.notna()
    if peak_candidates.any():
        peak_idx = dtg_up[peak_candidates].idxmax()
        peak_x = float(x.loc[peak_idx])
        peak_y = float(dtg_up.loc[peak_idx])
        ax2.scatter([peak_x], [peak_y], color="#c0392b", edgecolor="white", zorder=5)
        ax2.annotate(
            f"{peak_x:.0f} °C",
            xy=(peak_x, peak_y),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    ax1.set_title(str(sheet_name))
    ax1.legend([weight_line, dtg_line], ["Weight (%)", "-DTG (%/°C)"], loc="center left")
    ax1.grid(True, alpha=0.25)
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(sheet_name)).strip()
    fig.savefig(out_dir / f"{safe_name or 'plot'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
