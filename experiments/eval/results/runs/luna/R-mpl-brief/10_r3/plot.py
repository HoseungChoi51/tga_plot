from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/10_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

def safe_filename(name):
    return "".join(c if c.isalnum() or c in " -_." else "_" for c in str(name)).strip()

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(c).strip() for c in df.columns]
    temperature_col = next(c for c in df.columns if "temperature" in c.lower())
    weight_col = next(c for c in df.columns if "weight" in c.lower() and "%" in c)
    dtg_col = next(c for c in df.columns if "d.w" in c.lower() or "dtg" in c.lower())

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = temperature.notna() & weight.notna() & dtg.notna()
    temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
    dtg_line, = ax2.plot(temperature, -dtg, color="#c0392b", label="-DTG (%/°C)")

    # Residue at the measured point nearest 700 °C.
    residue_idx = (temperature - 700).abs().idxmin()
    residue_temp = temperature.loc[residue_idx]
    residue_value = weight.loc[residue_idx]
    ax1.scatter([residue_temp], [residue_value], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {residue_value:.2f}%",
        xy=(residue_temp, residue_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
    )

    # Highest upward-pointing DTG peak above 150 °C.
    peak_mask = temperature > 150
    peak_idx = (-dtg[peak_mask]).idxmax()
    peak_temp = temperature.loc[peak_idx]
    peak_value = -dtg.loc[peak_idx]
    ax2.scatter([peak_temp], [peak_value], color="#c0392b", zorder=5)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        xy=(peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
    )

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.3)
    ax1.legend([weight_line, dtg_line], ["Weight (%)", "-DTG (%/°C)"], loc="center left")

    fig.tight_layout()
    fig.savefig(OUT_DIR / f"{safe_filename(sheet_name)}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
