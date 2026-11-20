from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/21_r1/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Excel columns C, D, E correspond to zero-based positions 2, 3, 4.
with pd.ExcelFile(DATA_FILE) as workbook:
    for sheet_name in workbook.sheet_names:
        raw = pd.read_excel(
            workbook,
            sheet_name=sheet_name,
            header=None,
            usecols=[2, 3, 4],
            skiprows=8,
        )
        data = raw.apply(pd.to_numeric, errors="coerce").dropna()
        if data.empty:
            continue

        temperature = data.iloc[:, 0].to_numpy()
        weight = data.iloc[:, 1].to_numpy()
        dtg = data.iloc[:, 2].to_numpy()

        fig, ax1 = plt.subplots(figsize=(9, 6))
        ax1.plot(temperature, weight, color="#1f4e9c", label="Weight (%)")
        ax1.set_xlabel("Temperature (°C)")
        ax1.set_ylabel("Weight (%)", color="#1f4e9c")
        ax1.tick_params(axis="y", labelcolor="#1f4e9c")
        ax1.set_title(sheet_name)

        ax2 = ax1.twinx()
        dtg_up = -dtg
        ax2.plot(temperature, dtg_up, color="#c0392b", label="DTG (-%/°C)")
        ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
        ax2.tick_params(axis="y", labelcolor="#c0392b")

        # Mark the measured weight nearest 800 °C.
        residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
        ax1.scatter(
            temperature[residue_idx],
            weight[residue_idx],
            color="#1f4e9c",
            zorder=5,
        )
        ax1.annotate(
            f"Residue {weight[residue_idx]:.1f}%",
            (temperature[residue_idx], weight[residue_idx]),
            xytext=(8, 10),
            textcoords="offset points",
            color="#1f4e9c",
        )

        # Mark the highest upward-pointing DTG peak above 150 °C.
        eligible = np.flatnonzero(temperature > 150)
        if eligible.size:
            peak_idx = int(eligible[np.nanargmax(dtg_up[eligible])])
            ax2.scatter(
                temperature[peak_idx],
                dtg_up[peak_idx],
                color="#c0392b",
                zorder=5,
            )
            ax2.annotate(
                f"{temperature[peak_idx]:.0f} °C",
                (temperature[peak_idx], dtg_up[peak_idx]),
                xytext=(8, 10),
                textcoords="offset points",
                color="#c0392b",
            )

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")
        ax1.grid(True, alpha=0.25)
        fig.tight_layout()

        safe_name = "".join(
            char if char.isalnum() or char in ("-", "_") else "_" for char in sheet_name
        )
        fig.savefig(OUT_DIR / f"{safe_name}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
