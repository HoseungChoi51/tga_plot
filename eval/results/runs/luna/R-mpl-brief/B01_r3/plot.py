from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B01_r3/out"

# Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

out_dir = Path(OUT_DIR)
out_dir.mkdir(parents=True, exist_ok=True)

# Read the CSV, allowing common encodings.
try:
    data = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
except UnicodeDecodeError:
    data = pd.read_csv(DATA_FILE, encoding="cp949")

# Select the TGA columns from their headers.
def find_column(keywords):
    for col in data.columns:
        name = str(col).lower()
        if any(keyword in name for keyword in keywords):
            return col
    raise ValueError(f"Could not find a column matching {keywords}")

temperature_col = find_column(["temperature"])
weight_col = find_column(["weight (%)", "weight"])
dtg_col = find_column(["deriv", "dtg"])

temperature = pd.to_numeric(data[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(data[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(data[dtg_col], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(dtg)
temperature, weight, dtg = temperature[valid], weight[valid], dtg[valid]
order = np.argsort(temperature)
temperature, weight, dtg = temperature[order], weight[order], dtg[order]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

ax1.plot(temperature, weight, color="#1f4e9c", lw=1.8, label="Weight (%)")
ax2.plot(temperature, -dtg, color="#c0392b", lw=1.5, label="DTG")

# Highlight the three mass-loss intervals and annotate each above the plot curves.
intervals = [
    (120, 250, "H2O", "#77b5e5"),
    (430, 580, "CO", "#82c98a"),
    (640, 830, "CO2", "#f0b56b"),
]
ymin, ymax = np.nanmin(weight), np.nanmax(weight)
yrange = ymax - ymin if ymax > ymin else 1.0

for start, end, label, color in intervals:
    ax1.axvspan(start, end, color=color, alpha=0.22, zorder=0)
    ax1.text(
        (start + end) / 2,
        ymax + 0.035 * yrange,
        label,
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color="#333333",
        clip_on=False,
    )

# Standard TGA annotations: residue nearest 800 °C and highest DTG peak above 150 °C.
residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
residue_temp = temperature[residue_idx]
residue_value = weight[residue_idx]
ax1.scatter([residue_temp], [residue_value], color="#1f4e9c", s=35, zorder=5)
ax1.annotate(
    f"Residue {residue_value:.1f}%",
    (residue_temp, residue_value),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

peak_candidates = np.flatnonzero(temperature > 150)
if len(peak_candidates):
    peak_idx = peak_candidates[np.nanargmax((-dtg)[peak_candidates])]
    peak_temp = temperature[peak_idx]
    peak_value = -dtg[peak_idx]
    ax2.scatter([peak_temp], [peak_value], color="#c0392b", s=35, zorder=5)
    ax2.annotate(
        f"{peak_temp:.0f} °C",
        (peak_temp, peak_value),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=9,
    )

ax1.set_title("caox")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("DTG (-%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

ax1.set_xlim(np.nanmin(temperature), np.nanmax(temperature))
ax1.set_ylim(ymin - 0.05 * yrange, ymax + 0.12 * yrange)
fig.tight_layout()

fig.savefig(out_dir / "caox.png", dpi=300, bbox_inches="tight")
plt.close(fig)
