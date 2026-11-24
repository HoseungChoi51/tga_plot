from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/13_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(c).strip() for c in df.columns]

    temperature_col = next(
        (c for c in df.columns if "temperature" in c.lower()),
        df.columns[1] if len(df.columns) > 1 else None,
    )
    weight_col = next(
        (c for c in df.columns if "weight (mg)" in c.lower()),
        None,
    )
    dtg_col = next(
        (c for c in df.columns if "deriv" in c.lower() and "weight" in c.lower()),
        None,
    )

    if temperature_col is None or weight_col is None:
        continue

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight_mg = pd.to_numeric(df[weight_col], errors="coerce")
    valid = temperature.notna() & weight_mg.notna()
    temperature, weight_mg = temperature[valid], weight_mg[valid]

    if temperature.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax1.plot(temperature, weight_mg, color="#1f4e9c", label="Weight (mg)")
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (mg)")
    ax1.set_title(sheet_name)

    ax2 = ax1.twinx()
    if dtg_col is not None:
        dtg = pd.to_numeric(df[dtg_col], errors="coerce")
        dtg_valid = temperature.index.intersection(dtg.dropna().index)
        if len(dtg_valid):
            ax2.plot(
                temperature.loc[dtg_valid],
                -dtg.loc[dtg_valid],
                color="#c0392b",
                label="DTG",
            )
            ax2.set_ylabel("-DTG (%/°C)")

            peak_candidates = (temperature.loc[dtg_valid] > 150)
            peak_indices = temperature.loc[dtg_valid][peak_candidates].index
            if len(peak_indices):
                peak_idx = (-dtg.loc[peak_indices]).idxmax()
                peak_temp = temperature.loc[peak_idx]
                peak_value = -dtg.loc[peak_idx]
                ax2.scatter([peak_temp], [peak_value], color="#c0392b", zorder=5)
                ax2.annotate(
                    f"{peak_temp:.0f} °C",
                    (peak_temp, peak_value),
                    xytext=(6, 8),
                    textcoords="offset points",
                    color="#c0392b",
                )

    residue_idx = (temperature - 800).abs().idxmin()
    residue_temp = temperature.loc[residue_idx]
    residue_value = weight_mg.loc[residue_idx]
    ax1.scatter([residue_temp], [residue_value], color="#1f4e9c", zorder=5)
    ax1.annotate(
        f"Residue {residue_value:.1f} mg",
        (residue_temp, residue_value),
        xytext=(6, -16),
        textcoords="offset points",
        color="#1f4e9c",
    )

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    if handles1 or handles2:
        ax1.legend(handles1 + handles2, labels1 + labels2, loc="center left")

    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_ ." else "_" for ch in sheet_name).strip()
    fig.savefig(OUT_DIR / f"{safe_name or 'plot'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
