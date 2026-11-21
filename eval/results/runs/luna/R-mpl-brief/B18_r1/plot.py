from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-brief/B18_r1/out")
SHEET_NAME = "Annealed"

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the requested worksheet and identify the TGA columns by their headers.
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME)
df.columns = [str(c).strip() for c in df.columns]

def find_column(keywords):
    for column in df.columns:
        if any(word in column.lower() for word in keywords):
            return column
    return None

temperature_col = find_column(["temperature", "temp"])
weight_col = find_column(["weight"])
dtg_col = find_column(["deriv", "dtg"])

if temperature_col is None or weight_col is None or dtg_col is None:
    raise ValueError(f"Could not identify temperature, weight, and DTG columns: {list(df.columns)}")

data = df[[temperature_col, weight_col, dtg_col]].apply(pd.to_numeric, errors="coerce").dropna()
data = data.sort_values(temperature_col)
temperature = data[temperature_col].to_numpy()
weight = data[weight_col].to_numpy()
dtg = data[dtg_col].to_numpy()

# Estimate onset using the tangent-intersection method:
# locate the strongest mass-loss DTG peak above 150 °C, find the steepest
# weight-loss slope in that event, and intersect its tangent with the
# pre-event weight baseline.
valid_peaks = np.flatnonzero((temperature > 150) & (dtg < 0))
if len(valid_peaks) == 0:
    raise ValueError("No negative DTG peak above 150 °C was found.")

peak_idx = valid_peaks[np.argmin(dtg[valid_peaks])]
peak_temp = temperature[peak_idx]

# Use the weight-loss event surrounding the strongest DTG peak. The local
# window is bounded by nearby DTG minima/return-to-baseline locations when
# identifiable; otherwise use a 120 °C window before the peak.
left_candidates = np.flatnonzero(
    (temperature < peak_temp) & (temperature >= peak_temp - 180)
)
right_candidates = np.flatnonzero(
    (temperature > peak_temp) & (temperature <= peak_temp + 100)
)
left = left_candidates[0] if len(left_candidates) else 0
right = right_candidates[-1] + 1 if len(right_candidates) else len(temperature)

# Smooth local weight data slightly before calculating its derivative.
window = min( nine := 9, max(3, len(temperature[left:right]) // 10 * 2 + 1))
if window % 2 == 0:
    window -= 1
if window >= 3 and len(weight) >= window:
    smooth_weight = pd.Series(weight).rolling(window=window, center=True, min_periods=1).mean().to_numpy()
else:
    smooth_weight = weight

slope = np.gradient(smooth_weight, temperature)
event_indices = np.arange(left, right)
event_indices = event_indices[(temperature[event_indices] >= peak_temp - 100) & (temperature[event_indices] <= peak_temp + 20)]
if len(event_indices) == 0:
    event_indices = np.arange(max(0, peak_idx - 20), min(len(temperature), peak_idx + 1))

tangent_idx = event_indices[np.argmin(slope[event_indices])]
tangent_slope = slope[tangent_idx]
tangent_temp = temperature[tangent_idx]
tangent_weight = smooth_weight[tangent_idx]

# Baseline is the average mass in the stable region before the main event.
baseline_indices = np.flatnonzero(
    (temperature >= max(temperature.min(), tangent_temp - 180))
    & (temperature <= tangent_temp - 100)
)
if len(baseline_indices) < 3:
    baseline_indices = np.flatnonzero(temperature < tangent_temp)
baseline_weight = float(np.nanmedian(weight[baseline_indices])) if len(baseline_indices) else float(weight[0])

if np.isfinite(tangent_slope) and abs(tangent_slope) > 1e-12:
    onset_temp = tangent_temp + (baseline_weight - tangent_weight) / tangent_slope
else:
    onset_temp = tangent_temp

# Keep the estimate within the measured temperature range.
onset_temp = float(np.clip(onset_temp, temperature.min(), temperature.max()))
onset_weight = float(np.interp(onset_temp, temperature, weight))

fig, ax1 = plt.subplots(figsize=(9, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(temperature, weight, color="#1f4e9c", lw=2, label="Weight (%)")
line2, = ax2.plot(temperature, -dtg, color="#c0392b", lw=1.8, label="-DTG")
ax1.plot(onset_temp, onset_weight, marker="o", color="#111111", ms=6, zorder=5)
ax1.axvline(onset_temp, color="#444444", ls="--", lw=1.2, alpha=0.8)
ax1.annotate(
    f"Onset {onset_temp:.1f} °C",
    xy=(onset_temp, onset_weight),
    xytext=(10, 14),
    textcoords="offset points",
    ha="left",
    va="bottom",
    fontsize=10,
    color="#111111",
    arrowprops={"arrowstyle": "->", "color": "#444444", "lw": 1},
)

ax1.set_title(SHEET_NAME)
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)", color="#1f4e9c")
ax2.set_ylabel("-DTG (%/°C)", color="#c0392b")
ax1.tick_params(axis="y", labelcolor="#1f4e9c")
ax2.tick_params(axis="y", labelcolor="#c0392b")
ax1.grid(True, alpha=0.25)
ax1.legend([line1, line2], [line1.get_label(), line2.get_label()], loc="center left")
fig.tight_layout()

output_file = OUT_DIR / "Annealed_onset.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)
