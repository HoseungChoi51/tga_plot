from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/caox.csv")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B02_r2/out")

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load the CSV and use the columns identified in the supplied preview.
df = pd.read_csv(DATA_FILE)
df.columns = [str(c).strip() for c in df.columns]

temperature_col = next(c for c in df.columns if "Temperature" in c)
weight_col = next(c for c in df.columns if "Weight (%)" in c and "Deriv" not in c)
heat_flow_col = next(c for c in df.columns if "Heat Flow" in c)

temperature = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
heat_flow = pd.to_numeric(df[heat_flow_col], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(heat_flow)
temperature, weight, heat_flow = temperature[valid], weight[valid], heat_flow[valid]
order = np.argsort(temperature)
temperature, weight, heat_flow = temperature[order], weight[order], heat_flow[order]

# The instrument's heat-flow sign convention is not specified. Treat positive
# peaks as exothermic and negative peaks as endothermic, and label accordingly.
smooth_window = max(5, int(round(len(heat_flow) * 0.01)) | 1)
smooth_window = min(smooth_window, len(heat_flow) if len(heat_flow) % 2 else len(heat_flow) - 1)
if smooth_window >= 3:
    heat_flow_smooth = (
        pd.Series(heat_flow)
        .rolling(smooth_window, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )
else:
    heat_flow_smooth = heat_flow.copy()

amplitude = float(np.nanmax(heat_flow_smooth) - np.nanmin(heat_flow_smooth))
prominence = max(amplitude * 0.06, np.finfo(float).eps)
positive_peaks, positive_props = find_peaks(heat_flow_smooth, prominence=prominence)
negative_peaks, negative_props = find_peaks(-heat_flow_smooth, prominence=prominence)

# Select the two strongest endothermic peaks and the strongest exothermic peak.
endothermic = sorted(
    negative_peaks,
    key=lambda i: heat_flow_smooth[i],
)[:2]
exothermic = sorted(
    positive_peaks,
    key=lambda i: heat_flow_smooth[i],
    reverse=True,
)[:1]

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

ax1.plot(temperature, weight, color="#1f4e9c", linewidth=1.8, label="Weight (%)")
ax2.plot(
    temperature,
    heat_flow,
    color="#c0392b",
    linewidth=1.5,
    label="Heat Flow (W/g)",
)

# Residue annotation at the measured point nearest 800 °C.
residue_idx = int(np.nanargmin(np.abs(temperature - 800)))
ax1.scatter(
    temperature[residue_idx],
    weight[residue_idx],
    color="#1f4e9c",
    edgecolor="white",
    linewidth=0.8,
    zorder=5,
)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    xy=(temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

# Mark and label selected heat-flow peaks with their temperatures.
for index in endothermic:
    ax2.scatter(
        temperature[index], heat_flow[index], marker="v", s=55,
        color="#1f4e9c", edgecolor="white", linewidth=0.8, zorder=6
    )
    ax2.annotate(
        f"흡열 {temperature[index]:.0f} °C",
        xy=(temperature[index], heat_flow[index]),
        xytext=(0, -18),
        textcoords="offset points",
        ha="center",
        va="top",
        color="#1f4e9c",
        fontsize=9,
    )

for index in exothermic:
    ax2.scatter(
        temperature[index], heat_flow[index], marker="^", s=55,
        color="#c0392b", edgecolor="white", linewidth=0.8, zorder=6
    )
    ax2.annotate(
        f"발열 {temperature[index]:.0f} °C",
        xy=(temperature[index], heat_flow[index]),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        color="#c0392b",
        fontsize=9,
    )

ax1.set_title("caox")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("Heat Flow (W/g)", color="#c0392b")
ax1.tick_params(axis="y", colors="#1f4e9c")
ax2.tick_params(axis="y", colors="#c0392b")
ax1.grid(True, linestyle="--", alpha=0.35)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left")

fig.tight_layout()
fig.savefig(OUT_DIR / "caox.png", dpi=300, bbox_inches="tight")
plt.close(fig)
