from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/18_r2/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, raw in sheets.items():
    df = raw.copy()

    # TGA columns: temperature, weight, and derivative weight.
    normalized = {str(col).strip().lower(): col for col in df.columns}
    x_col = next((col for key, col in normalized.items() if "temperature" in key or "temp" in key), df.columns[1])
    weight_col = next((col for key, col in normalized.items() if "weight" in key and "%" in key), df.columns[2])
    dtg_col = next((col for key, col in normalized.items() if "d.w" in key or "dtg" in key or "derivative" in key), df.columns[3])

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna() & dtg.notna()
    x, weight, dtg = x[valid], weight[valid], dtg[valid]

    if x.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(x, -dtg, color="#c0392b", linewidth=1.5, label="DTG")

    # Residue at the measured point nearest 800 °C.
    residue_idx = (x - 800).abs().idxmin()
    residue_x = float(x.loc[residue_idx])
    residue_y = float(weight.loc[residue_idx])
    ax1.plot(residue_x, residue_y, "o", color="#1f4e9c", markersize=5)
    ax1.annotate(
        f"Residue {residue_y:.1f}%",
        xy=(residue_x, residue_y),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Highest upward DTG peak above 150 °C (DTG is plotted as -derivative).
    peak_candidates = (x > 150) & (-dtg > 0)
    if peak_candidates.any():
        peak_idx = (-dtg[peak_candidates]).idxmax()
        peak_x = float(x.loc[peak_idx])
        peak_y = float(-dtg.loc[peak_idx])
        ax2.plot(peak_x, peak_y, "o", color="#c0392b", markersize=5)
        ax2.annotate(
            f"{peak_x:.0f} °C",
            xy=(peak_x, peak_y),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    ax1.xaxis.set_major_locator(MultipleLocator(100))
    ax2.set_ylim(-0.05, 1.2)

    lines = ax1.get_lines()[:1] + ax2.get_lines()[:1]
    ax1.legend(lines, [line.get_label() for line in lines], loc="center left")
    ax1.grid(True, alpha=0.25)
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in str(sheet_name)).strip()
    fig.savefig(OUT_DIR / f"{safe_name or 'TGA'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
