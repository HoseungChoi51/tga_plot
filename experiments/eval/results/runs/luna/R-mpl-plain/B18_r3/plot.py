from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = Path("/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx")
OUT_DIR = Path("/home/chs/Work/tga_plot/eval/results/runs/luna/R-mpl-plain/B18_r3/out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Korean font and minus-sign rendering
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the Annealed TGA data
df = pd.read_excel(DATA_FILE, sheet_name="Annealed")
df.columns = [str(c).strip() for c in df.columns]

temperature = pd.to_numeric(df["Temperature (°C)"], errors="coerce").to_numpy()
weight = pd.to_numeric(df["Weight (%)"], errors="coerce").to_numpy()
derivative = pd.to_numeric(df["Deriv. Weight (%/°C)"], errors="coerce").to_numpy()

valid = np.isfinite(temperature) & np.isfinite(weight) & np.isfinite(derivative)
temperature, weight, derivative = temperature[valid], weight[valid], derivative[valid]

# Order points by temperature in case the worksheet is not already sorted.
order = np.argsort(temperature)
temperature, weight, derivative = temperature[order], weight[order], derivative[order]

# Estimate the principal decomposition onset from the strongest negative
# derivative peak. Fit a local linear baseline to the leading edge of that
# peak and extrapolate its intersection with the pre-event weight plateau.
peak_idx = int(np.argmin(derivative))
peak_temp = temperature[peak_idx]
peak_rate = derivative[peak_idx]

# Find the start of the main mass-loss event using the derivative magnitude.
# The local baseline is the median weight in the initial pre-event region.
pre_mask = (temperature < peak_temp) & (derivative > 0.10 * peak_rate)
if np.count_nonzero(pre_mask) < 5:
    pre_mask = (temperature < peak_temp) & (derivative > 0.05 * peak_rate)
if np.count_nonzero(pre_mask) < 5:
    pre_mask = temperature < peak_temp

pre_t = temperature[pre_mask]
pre_w = weight[pre_mask]
if pre_t.size:
    plateau_end = max(float(np.quantile(pre_t, 0.8)), float(temperature[0]))
    plateau_mask = temperature <= plateau_end
    if np.count_nonzero(plateau_mask) < 3:
        plateau_mask = np.arange(temperature.size) < max(3, int(0.05 * temperature.size))
    baseline_weight = float(np.median(weight[plateau_mask]))
else:
    baseline_weight = float(weight[0])

# Select the rising leading edge: derivative magnitude from 20% to 80% of
# the peak rate, before the peak.
leading_mask = (
    (temperature < peak_temp)
    & (derivative <= 0.0)
    & (derivative >= 0.20 * peak_rate)
)
if np.count_nonzero(leading_mask) < 3:
    leading_mask = (
        (temperature < peak_temp)
        & (derivative <= 0.0)
        & (derivative >= 0.10 * peak_rate)
    )

# If needed, use a short window immediately before the derivative minimum.
if np.count_nonzero(leading_mask) < 3:
    start = max(0, peak_idx - 12)
    leading_mask = np.zeros(temperature.size, dtype=bool)
    leading_mask[start:peak_idx] = True

lead_t = temperature[leading_mask]
lead_w = weight[leading_mask]

# Fit weight against temperature on the leading edge and extrapolate to the
# pre-event plateau weight. This is the tangent-intersection onset estimate.
slope, intercept = np.polyfit(lead_t, lead_w, 1)
if np.isclose(slope, 0.0):
    onset_temp = float(peak_temp)
else:
    onset_temp = float((baseline_weight - intercept) / slope)

# Keep the displayed onset within the measured temperature range.
onset_temp = float(np.clip(onset_temp, temperature.min(), peak_temp))
onset_weight = float(slope * onset_temp + intercept)

fig, ax = plt.subplots(figsize=(9, 6))
ax.plot(temperature, weight, color="#1f77b4", linewidth=2.2, label="Weight")
ax.set_xlabel("Temperature (°C)", fontsize=12)
ax.set_ylabel("Weight (%)", color="#1f77b4", fontsize=12)
ax.tick_params(axis="y", labelcolor="#1f77b4")
ax.set_xlim(float(temperature.min()), float(temperature.max()))
ax.grid(True, linestyle="--", alpha=0.35)

ax2 = ax.twinx()
ax2.plot(
    temperature,
    derivative,
    color="#d95f02",
    linewidth=1.5,
    alpha=0.9,
    label="Deriv. Weight",
)
ax2.set_ylabel("Deriv. Weight (%/°C)", color="#d95f02", fontsize=12)
ax2.tick_params(axis="y", labelcolor="#d95f02")

# Show the fitted leading-edge tangent and its intersection with the plateau.
tangent_t = np.linspace(onset_temp, peak_temp, 100)
ax.plot(
    tangent_t,
    slope * tangent_t + intercept,
    color="#2ca02c",
    linestyle="--",
    linewidth=1.8,
    label="Leading-edge tangent",
)
ax.axhline(
    baseline_weight,
    color="0.45",
    linestyle=":",
    linewidth=1.2,
    label="Pre-event baseline",
)
ax.axvline(
    onset_temp,
    color="#c51b7d",
    linestyle="--",
    linewidth=1.8,
)
ax.scatter(
    [onset_temp],
    [baseline_weight],
    color="#c51b7d",
    edgecolor="white",
    linewidth=0.8,
    s=65,
    zorder=6,
)
ax.annotate(
    f"Onset = {onset_temp:.1f} °C",
    xy=(onset_temp, baseline_weight),
    xytext=(12, 18),
    textcoords="offset points",
    color="#9e0e64",
    fontsize=11,
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#9e0e64", lw=1.2),
)

handles1, labels1 = ax.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax.legend(handles1 + handles2, labels1 + labels2, loc="best", frameon=True)

ax.set_title("Annealed — TGA onset by tangent extrapolation", fontsize=14)
fig.tight_layout()

output_path = OUT_DIR / "annealed_onset.png"
fig.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"Onset temperature: {onset_temp:.2f} °C")
print(f"Figure saved to: {output_path}")
