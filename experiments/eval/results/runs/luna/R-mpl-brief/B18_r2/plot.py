from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B18_r2/out")
SHEET_NAME = "Annealed"

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the requested sheet and identify TGA columns by their header names.
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
normalized = {str(c).strip().lower(): c for c in df.columns}

def find_column(needles):
    for name, original in normalized.items():
        if any(token in name for token in needles):
            return original
    raise ValueError(f"필요한 열을 찾을 수 없습니다: {needles}")

temperature_col = find_column(["temperature", "온도"])
weight_col = find_column(["weight", "중량", "무게"])
dtg_col = find_column(["deriv", "dtg"])

data = df[[temperature_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(temperature_col).drop_duplicates(subset=temperature_col)
temperature = data[temperature_col].to_numpy(dtype=float)
weight = data[weight_col].to_numpy(dtype=float)
dtg = data[dtg_col].to_numpy(dtype=float)

# DTG is negative during mass loss. Find the strongest loss peak above 150 °C,
# then estimate its onset by intersecting the pre-peak tangent at the steepest
# DTG descent with the pre-event weight baseline.
eligible = np.flatnonzero(temperature > 150)
if eligible.size == 0:
    raise ValueError("150 °C 초과 데이터가 없어 onset을 계산할 수 없습니다.")

peak_idx = eligible[np.argmin(dtg[eligible])]
pre_peak = np.flatnonzero((temperature > 150) & (np.arange(len(temperature)) < peak_idx))
if pre_peak.size < 3:
    raise ValueError("주요 DTG 피크 이전의 데이터가 부족해 onset을 계산할 수 없습니다.")

# Smooth DTG lightly to reduce point-to-point noise, preserving the measured
# location and scale; use the steepest downward slope before the main peak.
dt = np.gradient(temperature)
slope = np.gradient(dtg, temperature)
slope_window = pre_peak[2:]
tangent_idx = slope_window[np.argmin(slope[slope_window])]
tangent_slope = slope[tangent_idx]

# Use the local pre-event mass plateau as the baseline.
baseline_window = np.flatnonzero(
    (temperature >= max(temperature[0], temperature[tangent_idx] - 100))
    & (temperature <= temperature[tangent_idx] - 30)
)
if baseline_window.size < 3:
    baseline_window = pre_peak[: max(3, min(len(pre_peak), 20))]
baseline = float(np.median(weight[baseline_window]))

if not np.isfinite(tangent_slope) or abs(tangent_slope) < 1e-12:
    onset_temp = float(temperature[tangent_idx])
else:
    onset_temp = float(
        temperature[tangent_idx]
        + (baseline - weight[tangent_idx]) / np.gradient(weight, temperature)[tangent_idx]
    )

# Keep the reported onset within the physically relevant pre-peak interval.
onset_temp = float(np.clip(onset_temp, temperature[pre_peak[0]], temperature[peak_idx]))

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(temperature, weight, color="#1f4e9c", lw=1.8, label="Weight (%)")
line2, = ax2.plot(temperature, -dtg, color="#c0392b", lw=1.5, label="−DTG (%/°C)")

# Standard residue annotation at the measured point nearest 800 °C.
residue_idx = int(np.argmin(np.abs(temperature - 800)))
ax1.plot(temperature[residue_idx], weight[residue_idx], "o", color="#1f4e9c", ms=5)
ax1.annotate(
    f"Residue {weight[residue_idx]:.1f}%",
    (temperature[residue_idx], weight[residue_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#1f4e9c",
    fontsize=9,
)

# Standard DTG peak annotation.
ax2.plot(temperature[peak_idx], -dtg[peak_idx], "o", color="#c0392b", ms=5)
ax2.annotate(
    f"{temperature[peak_idx]:.0f} °C",
    (temperature[peak_idx], -dtg[peak_idx]),
    xytext=(8, 10),
    textcoords="offset points",
    color="#c0392b",
    fontsize=9,
)

# Mark onset temperature on the weight curve with a vertical guide and label.
onset_weight = float(np.interp(onset_temp, temperature, weight))
ax1.axvline(onset_temp, color="#555555", ls="--", lw=1.1, alpha=0.8)
ax1.plot(onset_temp, onset_weight, marker="D", color="#111111", ms=5)
ax1.annotate(
    f"Onset {onset_temp:.1f} °C",
    (onset_temp, onset_weight),
    xytext=(8, -22),
    textcoords="offset points",
    color="#111111",
    fontsize=10,
    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#999999", alpha=0.9),
)

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("−DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
fig.tight_layout()

fig.savefig(OUT_DIR / "Annealed_onset.png", dpi=300, bbox_inches="tight")
plt.close(fig)
