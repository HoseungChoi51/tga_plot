import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B18_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the Annealed sheet
df = pd.read_excel(DATA_FILE, sheet_name='Annealed')

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
d_weight = df['Deriv. Weight (%/°C)'].values

# Find onset temperature using extrapolation method
# The standard TGA onset is found by drawing a tangent at the point of maximum slope
# and extrapolating it to the baseline.

# 1. Identify the main decomposition peak in DTG
# Filter out initial noise or small fluctuations if any, focus on significant mass loss
# We look for the minimum value in d_weight (most negative derivative)
min_idx = np.argmin(d_weight)
peak_temp = temp[min_idx]
peak_dtg = d_weight[min_idx]

# 2. Determine the baseline weight before decomposition
# Use data from low temperatures where weight is stable (e.g., first 50 degrees or until weight drops significantly)
baseline_mask = temp < 100
if np.sum(baseline_mask) > 5:
    baseline_weight = np.mean(weight[baseline_mask])
else:
    baseline_weight = weight[0]

# 3. Find the steepest slope region around the peak to fit a tangent line
# We select points near the inflection point leading to the peak.
# A common approach is to find the point of maximum slope magnitude on the descending side of the peak.
# Let's take a window around the peak index.
window_size = 50 # Adjust based on data density
start_idx = max(0, min_idx - window_size)
end_idx = min(len(temp), min_idx + window_size)

temp_window = temp[start_idx:end_idx]
weight_window = weight[start_idx:end_idx]

# Fit a linear model to the steepest part of the curve to approximate the tangent
# To be more robust, we can use the points where the second derivative changes sign or just fit a line 
# to the section with the highest absolute slope.
# Let's calculate slopes between consecutive points
slopes = np.diff(weight_window) / np.diff(temp_window)
# Find the index of the steepest slope within the window
steepest_slope_idx = np.argmin(slopes) # Most negative slope

# Select a subset of points around the steepest slope for linear fitting
fit_points_count = 10
fit_start = max(0, steepest_slope_idx - fit_points_count // 2)
fit_end = min(len(temp_window), steepest_slope_idx + fit_points_count // 2 + 1)

t_fit = temp_window[fit_start:fit_end]
w_fit = weight_window[fit_start:fit_end]

# Linear regression to get slope (m) and intercept (c)
coeffs = np.polyfit(t_fit, w_fit, 1)
m = coeffs[0]
c = coeffs[1]

# Calculate onset temperature: intersection of the tangent line and the baseline
# Equation: y = m * x + c
# Baseline: y = baseline_weight
# onset_T = (baseline_weight - c) / m
onset_temperature = (baseline_weight - c) / m

# Ensure the calculated onset is reasonable (within range and positive)
if not (np.min(temp) <= onset_temperature <= np.max(temp)):
    # Fallback: if extrapolation fails, use the temperature where weight drops by a certain % (e.g., 5%)
    # Or simply the temperature at the start of significant deviation
    diff_from_baseline = baseline_weight - weight
    threshold = 0.05 * baseline_weight # 5% weight loss
    indices_above_threshold = np.where(diff_from_baseline > threshold)[0]
    if len(indices_above_threshold) > 0:
        onset_temperature = temp[indices_above_threshold[0]]
    else:
        onset_temperature = temp[min_idx] # Last resort

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

color1 = 'tab:red'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
ax1.plot(temp, weight, color=color1, label='TGA (Annealed)', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# Add vertical line for onset temperature
ax1.axvline(x=onset_temperature, color='green', linestyle='--', linewidth=2, label=f'외삽 개시 온도: {onset_temperature:.2f} °C')

# Annotate the onset point on the graph
ax1.annotate(f'{onset_temperature:.2f} °C', xy=(onset_temperature, baseline_weight), 
             xytext=(onset_temperature + 20, baseline_weight - 10),
             arrowprops=dict(facecolor='green', shrink=0.05),
             fontsize=10, color='green')

# Draw the tangent line segment for visualization
# Extend the tangent line slightly beyond the fit range for visual clarity
t_tangent_plot = np.linspace(onset_temperature, onset_temperature + 50, 100)
w_tangent_plot = m * t_tangent_plot + c
# Only plot the part that makes sense (above baseline or close to it initially)
valid_tangent = (t_tangent_plot >= onset_temperature) & (w_tangent_plot <= baseline_weight + 5)
ax1.plot(t_tangent_plot[valid_tangent], w_tangent_plot[valid_tangent], color='green', linestyle=':', linewidth=1.5, label='접선 (Extrapolation)')

# Secondary axis for DTG
ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
ax2.plot(temp, d_weight, color=color2, label='DTG (Annealed)', linewidth=2, alpha=0.7)
ax2.tick_params(axis='y', labelcolor=color2)

# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', fontsize=9)

plt.title('Annealed 시료의 TGA/DTG 곡선 및 외삽 개시 온도 분석', fontsize=14)
fig.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, 'annealed_onset_analysis.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Figure saved to {output_path}")
print(f"Calculated Onset Temperature: {onset_temperature:.2f} °C")
