from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B24_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

sheet_name = "PE"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Identify the temperature, weight, and derivative-weight columns by their headers.
def find_column(keywords):
    for col in df.columns:
        if any(word in str(col).lower() for word in keywords):
            return col
    raise ValueError(f"Could not find a column matching {keywords}")

temperature_col = find_column(["temperature"])
weight_col = find_column(["weight (%)", "weight(%)"])
dtg_col = find_column(["deriv", "dtg"])

temperature_c = pd.to_numeric(df[temperature_col], errors="coerce").to_numpy()
weight = pd.to_numeric(df[weight_col], errors="coerce").to_numpy()
dtg = pd.to_numeric(df[dtg_col], errors="coerce").to_numpy()
valid = np.isfinite(temperature_c) & np.isfinite(weight) & np.isfinite(dtg)

temperature_c = temperature_c[valid]
weight = weight[valid]
dtg = dtg[valid]
temperature_k = temperature_c + 273.15

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

weight_line, = ax1.plot(
    temperature_k, weight, color="#1f4e9c", label="Weight (%)", linewidth=1.8
)
dtg_up = -dtg
dtg_line, = ax2.plot(
    temperature_k, dtg_up, color="#c0392b", label="DTG (-Derivative)", linewidth=1.5
)

# Residue: weight at the measured point nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature_c - 800)))
residue_temp_k = temperature_k[residue_idx]
residue_weight = weight[residue_idx]
ax1.plot(
    residue_temp_k, residue_weight, marker="o", color="#1f4e9c",
    markersize=6, linestyle="None", zorder=5
)
ax1.annotate(
    f"Residue {residue_weight:.1f}%",
    xy=(residue_temp_k, residue_weight),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=10,
)

# Peak: highest upward-pointing DTG peak above 150 °C.
peak_candidates = np.flatnonzero(temperature_c > 150)
if peak_candidates.size:
    peak_idx = peak_candidates[np.argmax(dtg_up[peak_candidates])]
    peak_temp_k = temperature_k[peak_idx]
    peak_dtg = dtg_up[peak_idx]
    ax2.plot(
        peak_temp_k, peak_dtg, marker="o", color="#c0392b",
        markersize=6, linestyle="None", zorder=5
    )
    ax2.annotate(
        f"{peak_temp_k:.0f} K",
        xy=(peak_temp_k, peak_dtg),
        xytext=(8, 10),
        textcoords="offset points",
        color="#c0392b",
        fontsize=10,
    )

ax1.set_title(sheet_name)
ax1.set_xlabel("Temperature (K)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("DTG (-Derivative Weight, %/°C)")
ax1.legend(
    handles=[weight_line, dtg_line],
    loc="center left",
    frameon=True,
)
ax1.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUT_DIR / "PE_temperature_K.png", dpi=300, bbox_inches="tight")
plt.close(fig)
