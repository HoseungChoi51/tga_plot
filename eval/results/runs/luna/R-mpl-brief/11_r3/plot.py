from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/11_r3/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_column(columns, terms):
    """Return the first column whose normalized name contains one of the terms."""
    normalized = {col: str(col).strip().lower().replace(" ", "") for col in columns}
    for term in terms:
        term = term.lower().replace(" ", "")
        for col, name in normalized.items():
            if term in name:
                return col
    return None


sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    x_col = find_column(df.columns, ["temperature", "temp", "온도"])
    weight_col = find_column(df.columns, ["weight(%)", "weight%", "weight", "중량"])
    dtg_col = find_column(df.columns, ["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        # Fall back to the standard TGA column order: B = temperature, C = weight, D = DTG.
        if df.shape[1] < 4:
            continue
        x_col, weight_col, dtg_col = df.columns[1], df.columns[2], df.columns[3]

    x = pd.to_numeric(df[x_col], errors="coerce")
    weight = pd.to_numeric(df[weight_col], errors="coerce")
    dtg = pd.to_numeric(df[dtg_col], errors="coerce")
    valid = x.notna() & weight.notna()
    x, weight = x[valid], weight[valid]
    dtg = dtg.loc[x.index]

    if x.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(8, 6))
    ax1.plot(x, weight, color="#1f4e9c", linewidth=1.8, label="Weight")
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")

    ax2 = ax1.twinx()
    valid_dtg = dtg.notna()
    ax2.plot(
        x[valid_dtg],
        -dtg[valid_dtg],
        color="#c0392b",
        linewidth=1.5,
        label="DTG",
    )
    ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    # Mark and label the weight at the measured point nearest 800 °C.
    nearest_idx = (x - 800).abs().idxmin()
    residue_x = float(x.loc[nearest_idx])
    residue_y = float(weight.loc[nearest_idx])
    ax1.scatter(
        [residue_x], [residue_y], color="#1f4e9c", edgecolor="white",
        linewidth=0.7, s=45, zorder=5
    )
    ax1.annotate(
        f"Residue {residue_y:.1f}%",
        (residue_x, residue_y),
        xytext=(8, 10),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    # Combine both axes' handles in a center-left legend.
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        loc="center left",
        frameon=False,
    )

    ax1.set_title(str(sheet_name))
    ax1.grid(False)
    fig.tight_layout()

    safe_name = "".join(
        char if char.isalnum() or char in "-_ ." else "_" for char in str(sheet_name)
    ).strip().replace(" ", "_")
    fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
