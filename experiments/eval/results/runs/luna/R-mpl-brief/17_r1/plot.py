from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/17_r1/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheets = pd.read_excel(DATA_FILE, sheet_name=None)

for sheet_name, df in sheets.items():
    df.columns = [str(column).strip() for column in df.columns]

    temperature_col = next(
        (column for column in df.columns if "temperature" in column.lower()),
        df.columns[1],
    )
    weight_col = next(
        (column for column in df.columns if "weight" in column.lower() and "d.w" not in column.lower()),
        df.columns[2],
    )
    dtg_col = next(
        (column for column in df.columns if "d.w" in column.lower() or "dtg" in column.lower()),
        df.columns[3],
    )

    data = df[[temperature_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
    temperature = data[temperature_col].to_numpy()
    weight = data[weight_col].to_numpy()
    dtg_up = -data[dtg_col].to_numpy()

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()

    weight_line, = ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
    dtg_line, = ax2.plot(temperature, dtg_up, color="#c0392b", label="DTG (%/°C)")

    ax1.set_title(sheet_name)
    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Weight (%)", color="#1f4e9c")
    ax2.set_ylabel("DTG (%/°C)", color="#c0392b")
    ax1.tick_params(axis="y", labelcolor="#1f4e9c")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.grid(True, alpha=0.3)

    residue_index = int(np.argmin(np.abs(temperature - 800)))
    ax1.scatter(
        temperature[residue_index],
        weight[residue_index],
        color="#1f4e9c",
        zorder=5,
    )
    ax1.annotate(
        f"Residue {weight[residue_index]:.1f}%",
        (temperature[residue_index], weight[residue_index]),
        xytext=(8, 8),
        textcoords="offset points",
        color="#1f4e9c",
    )

    eligible = np.flatnonzero(temperature > 150)
    if eligible.size:
        peak_index = int(eligible[np.argmax(dtg_up[eligible])])
        ax2.scatter(temperature[peak_index], dtg_up[peak_index], color="#c0392b", zorder=5)
        ax2.annotate(
            f"{temperature[peak_index]:.0f} °C",
            (temperature[peak_index], dtg_up[peak_index]),
            xytext=(8, 8),
            textcoords="offset points",
            color="#c0392b",
        )

    ax1.legend([weight_line, dtg_line], ["Weight (%)", "DTG (%/°C)"], loc="center left")
    fig.tight_layout()

    output_path = OUT_DIR / f"{sheet_name}.png"
    fig.savefig(output_path, dpi=600, bbox_inches="tight")
    plt.close(fig)
