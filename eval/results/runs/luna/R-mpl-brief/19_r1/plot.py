from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/19_r1/out"

TEXT_COLOR = "gray"
FONT_SIZE = 13
WEIGHT_COLOR = "#1f4e9c"
DTG_COLOR = "#c0392b"

plt.rcParams.update({
    "font.family": "Noto Sans CJK KR",
    "font.size": FONT_SIZE,
    "text.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "axes.titlecolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "legend.labelcolor": TEXT_COLOR,
})

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(col).strip() for col in df.columns]

    def find_column(candidates):
        for col in df.columns:
            normalized = col.lower().replace(" ", "")
            if any(candidate in normalized for candidate in candidates):
                return col
        return None

    x_col = find_column(["temperature", "temp"])
    weight_col = find_column(["weight"])
    dtg_col = find_column(["d.w", "dtg", "derivative"])

    if x_col is None or weight_col is None or dtg_col is None:
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        if len(numeric_cols) < 3:
            continue
        x_col, weight_col, dtg_col = numeric_cols[1:4]

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    temperature = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg = data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    ax1.plot(temperature, weight, color=WEIGHT_COLOR, linewidth=1.8, label="Weight (%)")
    ax2.plot(temperature, -dtg, color=DTG_COLOR, linewidth=1.5, label="-DTG (%/°C)")

    residue_idx = int(np.argmin(np.abs(temperature - 800)))
    residue_temp = temperature[residue_idx]
    residue = weight[residue_idx]
    ax1.scatter([residue_temp], [residue], color=WEIGHT_COLOR, zorder=4)
    ax1.annotate(
        f"Residue {residue:.1f}%",
        xy=(residue_temp, residue),
        xytext=(8, 10),
        textcoords="offset points",
        color=TEXT_COLOR,
        fontsize=FONT_SIZE,
    )

    peak_mask = temperature > 150
    if peak_mask.any():
        peak_indices = np.flatnonzero(peak_mask)
        peak_idx = peak_indices[np.argmax(-dtg[peak_mask])]
        peak_temp = temperature[peak_idx]
        peak_value = -dtg[peak_idx]
        ax2.scatter([peak_temp], [peak_value], color=DTG_COLOR, zorder=4)
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            xy=(peak_temp, peak_value),
            xytext=(8, 10),
            textcoords="offset points",
            color=TEXT_COLOR,
            fontsize=FONT_SIZE,
        )

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)")
    ax2.set_ylabel("DTG (%/°C)")

    ax1.tick_params(axis="both", labelsize=FONT_SIZE, colors=TEXT_COLOR)
    ax2.tick_params(axis="y", labelsize=FONT_SIZE, colors=TEXT_COLOR)
    ax1.spines["left"].set_color(TEXT_COLOR)
    ax1.spines["bottom"].set_color(TEXT_COLOR)
    ax1.spines["top"].set_color(TEXT_COLOR)
    ax2.spines["right"].set_color(TEXT_COLOR)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

    fig.tight_layout()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in sheet_name).strip()
    fig.savefig(out_dir / f"{safe_name or 'TGA'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
