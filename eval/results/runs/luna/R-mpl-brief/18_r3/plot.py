from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/18_r3/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    columns = {str(col).strip().lower(): col for col in df.columns}

    def find_column(*needles):
        for needle in needles:
            for normalized, original in columns.items():
                if needle in normalized:
                    return original
        return None

    x_col = find_column("temperature", "temp")
    weight_col = find_column("weight")
    dtg_col = find_column("d.w", "dtg", "derivative")

    if x_col is None or weight_col is None or dtg_col is None:
        numeric = df.select_dtypes(include="number").columns.tolist()
        if len(numeric) < 3:
            continue
        x_col, weight_col, dtg_col = numeric[1], numeric[2], numeric[3]

    data = df[[x_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        continue

    temperature = data[x_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg_up = -data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(9, 6))
    ax2 = ax1.twinx()

    ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
    ax2.plot(temperature, dtg_up, color="#c0392b", linewidth=1.5, label="DTG")

    ax1.set_title(str(sheet_name))
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    x_min = float(np.nanmin(temperature))
    x_max = float(np.nanmax(temperature))
    first_tick = np.ceil(x_min / 100) * 100
    ax1.set_xticks(np.arange(first_tick, x_max + 1, 100))
    ax2.set_ylim(-0.05, 1.2)

    residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
    residue_temp = temperature[residue_idx]
    residue_value = weight[residue_idx]
    ax1.plot(residue_temp, residue_value, "o", color="#1f4e9c", markersize=5)
    ax1.annotate(
        f"Residue {residue_value:.1f}%",
        (residue_temp, residue_value),
        xytext=(7, 9),
        textcoords="offset points",
        color="#1f4e9c",
        fontsize=9,
    )

    eligible = np.flatnonzero(temperature > 150)
    if eligible.size:
        peak_idx = int(eligible[np.argmax(dtg_up[eligible])])
        peak_temp = temperature[peak_idx]
        peak_value = dtg_up[peak_idx]
        ax2.plot(peak_temp, peak_value, "o", color="#c0392b", markersize=5)
        ax2.annotate(
            f"{peak_temp:.0f} °C",
            (peak_temp, peak_value),
            xytext=(7, 9),
            textcoords="offset points",
            color="#c0392b",
            fontsize=9,
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")
    ax1.grid(True, alpha=0.25)
    fig.tight_layout()

    safe_name = "".join(c if c.isalnum() or c in "-_ ." else "_" for c in str(sheet_name)).strip()
    fig.savefig(out_dir / f"{safe_name or 'plot'}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
