from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B21_r2/out")

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False


def find_column(columns, keywords):
    for column in columns:
        name = str(column).strip().lower()
        if all(keyword in name for keyword in keywords):
            return column
    raise ValueError(f"Could not find a column matching: {keywords}")


OUT_DIR.mkdir(parents=True, exist_ok=True)
data = pd.read_excel(DATA_FILE, sheet_name="Raw")

temperature_col = find_column(data.columns, ["temperature"])
weight_col = find_column(data.columns, ["weight"])
dtg_col = find_column(data.columns, ["deriv"])

temperature = pd.to_numeric(data[temperature_col], errors="coerce")
weight = pd.to_numeric(data[weight_col], errors="coerce")
dtg = pd.to_numeric(data[dtg_col], errors="coerce")

valid = temperature.notna() & weight.notna() & dtg.notna()
temperature = temperature[valid].to_numpy()
weight = weight[valid].to_numpy()
dtg = dtg[valid].to_numpy()

residue_idx = int(np.argmin(np.abs(temperature - 800)))
peak_candidates = np.flatnonzero(temperature > 150)
if peak_candidates.size:
    peak_idx = int(peak_candidates[np.argmax(-dtg[peak_candidates])])
else:
    peak_idx = int(np.argmax(-dtg))

fig, ax1 = plt.subplots(figsize=(8, 6))
weight_line, = ax1.plot(
    temperature, weight, color="#1f4e9c", linewidth=2, label="Weight"
)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax1.set_title("Raw")

ax2 = ax1.twinx()
dtg_line, = ax2.plot(
    temperature, -dtg, color="#c0392b", linewidth=1.8, label="DTG"
)
ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
ax2.tick_params(axis="y", labelcolor="#c0392b")

ax1.plot(
    temperature[residue_idx], weight[residue_idx],
    marker="o", color="#1f4e9c", markersize=6
)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10), textcoords="offset points",
    color="#1f4e9c", fontsize=9
)

ax2.plot(
    temperature[peak_idx], -dtg[peak_idx],
    marker="o", color="#c0392b", markersize=6
)
ax2.annotate(
    f"{temperature[peak_idx]:.0f} °C",
    (temperature[peak_idx], -dtg[peak_idx]),
    xytext=(8, 10), textcoords="offset points",
    color="#c0392b", fontsize=9
)

ax1.legend([weight_line, dtg_line], ["Weight", "DTG"], loc="center left")
ax1.invert_xaxis()
fig.tight_layout()
fig.savefig(OUT_DIR / "Raw.png", dpi=300, bbox_inches="tight")
plt.close(fig)
