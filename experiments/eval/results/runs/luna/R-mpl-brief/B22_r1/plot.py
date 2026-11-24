from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B22_r1/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_excel(DATA_FILE, sheet_name="Raw")

# Identify the TGA columns by their names.
def find_column(keyword):
    matches = [col for col in df.columns if keyword.lower() in str(col).lower()]
    if not matches:
        raise ValueError(f"'{keyword}' 열을 찾을 수 없습니다: {list(df.columns)}")
    return matches[0]

temperature_col = find_column("Temperature")
weight_col = find_column("Weight")
dtg_col = find_column("Deriv")

data = df[[temperature_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
temperature = data[temperature_col].to_numpy()
weight = data[weight_col].to_numpy()
dtg = data[dtg_col].to_numpy()

# Set the measured weight nearest 150 °C to 100% (dry-basis normalization).
idx_150 = int(np.argmin(np.abs(temperature - 150.0)))
weight_at_150 = weight[idx_150]
if not np.isfinite(weight_at_150) or weight_at_150 == 0:
    raise ValueError("150 °C 기준 무게가 유효하지 않아 정규화할 수 없습니다.")

scale = 100.0 / weight_at_150
weight_dry = weight * scale
dtg_dry = dtg * scale

# Residue: normalized weight at the measured point nearest 800 °C.
idx_800 = int(np.argmin(np.abs(temperature - 800.0)))

# Peak: highest positive -DTG peak above 150 °C.
candidate_indices = np.flatnonzero(temperature > 150.0)
if candidate_indices.size == 0:
    raise ValueError("150 °C 초과 구간이 없습니다.")
local_peaks, _ = find_peaks(-dtg_dry[candidate_indices])
if local_peaks.size:
    peak_indices = candidate_indices[local_peaks]
else:
    peak_indices = candidate_indices
idx_peak = int(peak_indices[np.argmax(-dtg_dry[peak_indices])])

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(
    temperature, weight_dry, color="#1f4e9c", linewidth=2, label="Weight (dry basis)"
)
line2, = ax2.plot(
    temperature, -dtg_dry, color="#c0392b", linewidth=1.8, label="-DTG (dry basis)"
)

ax1.scatter(
    temperature[idx_800], weight_dry[idx_800],
    color="#1f4e9c", edgecolor="white", linewidth=0.8, zorder=5
)
ax1.annotate(
    f"Residue {weight_dry[idx_800]:.1f}%",
    (temperature[idx_800], weight_dry[idx_800]),
    xytext=(8, 10), textcoords="offset points",
    color="#1f4e9c", fontsize=10
)

ax2.scatter(
    temperature[idx_peak], -dtg_dry[idx_peak],
    color="#c0392b", edgecolor="white", linewidth=0.8, zorder=5
)
ax2.annotate(
    f"{temperature[idx_peak]:.0f} °C",
    (temperature[idx_peak], -dtg_dry[idx_peak]),
    xytext=(8, 10), textcoords="offset points",
    color="#c0392b", fontsize=10
)

ax1.set_title("Raw")
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("-DTG (%/°C)")
ax1.grid(True, linestyle="--", alpha=0.35)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
fig.tight_layout()

fig.savefig(OUT_DIR / "Raw_dry_basis.png", dpi=300, bbox_inches="tight")
plt.close(fig)
