from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/13_r2/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)
for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    def find_column(candidates):
        for col in df.columns:
            normalized = col.lower().replace(" ", "")
            if any(candidate.lower().replace(" ", "") in normalized for candidate in candidates):
                return col
        return None

    temperature_col = find_column(["Temperature (°C)", "Temperature"])
    weight_mg_col = find_column(["Weight (mg)"])
    dtg_col = find_column(["Deriv. Weight", "DTG"])

    if temperature_col is None or weight_mg_col is None or dtg_col is None:
        continue

    temperature = pd.to_numeric(df[temperature_col], errors="coerce")
    weight_mg = pd.to_numeric(df[weight_mg_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = temperature.notna() & weight_mg.notna()
    temperature = temperature[valid]
    weight_mg = weight_mg[valid]
    dtg = dtg.loc[temperature.index]

    if temperature.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax1.plot(temperature, weight_mg, color="#1f4e9c", label="Weight (mg)")
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (mg)")
    ax1.set_title(sheet_name)

    ax2 = ax1.twinx()
    dtg_valid = dtg.notna()
    ax2.plot(
        temperature[dtg_valid],
        -dtg[dtg_valid],
        color="#c0392b",
        label="DTG",
    )
    ax2.set_ylabel("DTG (%/°C)")

    # Residue at the measured temperature nearest 800 °C.
    residue_idx = (temperature - 800).abs().idxmin()
    residue_x = float(temperature.loc[residue_idx])
    residue_y = float(weight_mg.loc[residue_idx])
    ax1.plot(residue_x, residue_y, "o", color="#1f4e9c")
    ax1.annotate(
        f"Residue {residue_y:.1f} mg",
        (residue_x, residue_y),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
    )

    # Highest positive -DTG peak above 150 °C.
    peak_candidates = dtg.notna() & (temperature > 150)
    if peak_candidates.any():
        peak_idx = (-dtg[peak_candidates]).idxmax()
        peak_x = float(temperature.loc[peak_idx])
        peak_y = float(-dtg.loc[peak_idx])
        ax2.plot(peak_x, peak_y, "o", color="#c0392b")
        ax2.annotate(
            f"{peak_x:.0f} °C",
            (peak_x, peak_y),
            xytext=(8, 10),
            textcoords="offset points",
            color="#c0392b",
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in sheet_name)
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
