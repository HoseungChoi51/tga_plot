from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B15_r1/out"

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

sheets = ["PE", "PVC", "PET"]
colors = {"PE": "#1f4e9c", "PVC": "#2e8b57", "PET": "#8e44ad"}
dtg_color = "#c0392b"

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()
legend_handles = []

with pd.ExcelFile(DATA_FILE) as workbook:
    for sheet in sheets:
        df = pd.read_excel(workbook, sheet_name=sheet)
        df.columns = [str(col).strip() for col in df.columns]

        temperature_col = next(
            col for col in df.columns
            if "temperature" in col.lower() or "온도" in col
        )
        weight_col = next(
            col for col in df.columns
            if "weight" in col.lower() and "deriv" not in col.lower()
        )
        dtg_col = next(
            col for col in df.columns
            if "deriv" in col.lower() or "dtg" in col.lower()
        )

        temp = pd.to_numeric(df[temperature_col], errors="coerce")
        weight = pd.to_numeric(df[weight_col], errors="coerce")
        dtg = pd.to_numeric(df[dtg_col], errors="coerce")
        valid = temp.notna() & weight.notna() & dtg.notna()
        temp, weight, dtg = temp[valid], weight[valid], dtg[valid]

        line, = ax1.plot(
            temp, weight, color=colors[sheet], linewidth=1.8, label=f"{sheet} 중량"
        )
        ax2.plot(
            temp, -dtg, color=dtg_color, linewidth=1.2, linestyle="--",
            alpha=0.75, label=f"{sheet} DTG"
        )
        legend_handles.append(line)

        residue_idx = (temp - 800).abs().idxmin()
        ax1.plot(
            temp.loc[residue_idx], weight.loc[residue_idx],
            marker="o", color=colors[sheet], markersize=5
        )
        ax1.annotate(
            f"{sheet} 잔류량 {weight.loc[residue_idx]:.1f}%",
            (temp.loc[residue_idx], weight.loc[residue_idx]),
            xytext=(5, 5), textcoords="offset points",
            color=colors[sheet], fontsize=8
        )

        peak_candidates = dtg[temp > 150]
        if not peak_candidates.empty:
            peak_idx = peak_candidates.idxmin()
            peak_temp = temp.loc[peak_idx]
            peak_height = -dtg.loc[peak_idx]
            ax2.plot(peak_temp, peak_height, marker="^", color=dtg_color, markersize=5)
            ax2.annotate(
                f"{sheet} {peak_temp:.0f} °C",
                (peak_temp, peak_height),
                xytext=(5, 5), textcoords="offset points",
                color=dtg_color, fontsize=8
            )

ax1.set_title("PE, PVC, PET")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (-Derivative Weight, %/°C)")
ax1.set_xlim(30, 900)
ax1.grid(True, alpha=0.25)

ax1.legend(
    handles=legend_handles,
    labels=[f"{sheet} 중량" for sheet in sheets],
    loc="center left",
    bbox_to_anchor=(1.16, 0.5),
    frameon=False
)
fig.subplots_adjust(right=0.78)
fig.savefig(out_dir / "polymers_overlay.png", dpi=300, bbox_inches="tight")
plt.close(fig)
