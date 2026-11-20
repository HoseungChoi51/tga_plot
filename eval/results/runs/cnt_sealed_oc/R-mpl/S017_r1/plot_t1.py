import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Set Korean font and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet from Excel file
file_path = "data/tga_batches.xlsx"
sheet_name = "R2-260616-1"

# Load data
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Ensure column names match exactly as per preview (handling potential whitespace)
cols = df.columns.tolist()
time_col = [c for c in cols if '시간' in str(c)][0]
temp_col = [c for c in cols if '온도' in str(c)][0]
weight_col = [c for c in cols if '중량' in str(c) and '미분' not in str(c)][0]
dtg_col = [c for c in cols if '미분' in str(c)][0]

# Extract relevant columns and clean data
temps = df[temp_col].values
weights = df[weight_col].values
dtgs = df[dtg_col].values

# Filter for 450-800 °C range to find DTG maximum
mask_450_800 = (temps >= 450) & (temps <= 800)
temps_range = temps[mask_450_800]
dtgs_range = dtgs[mask_450_800]

if len(dtgs_range) == 0:
    raise ValueError("No data found in 450-800 °C range")

# Find the index of maximum DTG value in this range (steepest drop)
max_dtg_idx_in_range = np.argmax(dtgs_range)
peak_temp = temps_range[max_dtg_idx_in_range]
peak_dtg_val = dtgs_range[max_dtg_idx_in_range]

# Get the weight at 500 °C for baseline
# Interpolate to find exact weight at 500 °C since it might not be a discrete point
weight_at_500 = np.interp(500.0, temps, weights)
baseline_weight = weight_at_500

# Calculate Extrapolated Onset Temperature
# Method: Tangent at peak DTG intersects with the baseline (horizontal line at weight@500)
# Slope of tangent at peak is approximately the DTG value itself (dW/dT).
# However, DTG is often smoothed or calculated via finite differences. 
# The prompt says "tangent at the steepest drop". 
# Equation of tangent line passing through (T_peak, W_peak):
# W - W_peak = m * (T - T_peak)
# Here m is the slope dW/dT at T_peak. Note: The data column is "미분중량 (%/°C)", which IS dW/dT.
# So slope m = peak_dtg_val.
# We need W_peak (weight at T_peak).
w_at_peak = np.interp(peak_temp, temps, weights)

# Line equation: W(T) = w_at_peak + peak_dtg_val * (T - peak_temp)
# Baseline equation: W(T) = baseline_weight
# Intersection: baseline_weight = w_at_peak + peak_dtg_val * (T_onset - peak_temp)
# Solve for T_onset:
# T_onset - peak_temp = (baseline_weight - w_at_peak) / peak_dtg_val
# T_onset = peak_temp + (baseline_weight - w_at_peak) / peak_dtg_val

# Careful with sign: DTG is negative during mass loss? 
# Preview shows DTG values like -0.012 to 2.04. Wait, usually TG drops so dW/dT is negative.
# But the max value in the list is positive (2.07). Let's check typical TGA behavior.
# If "미분중량" is defined as -dW/dT (common convention for peaks), then slope is positive.
# If it is dW/dT, slope is negative.
# Given the range includes positive numbers up to ~2, and standard TG curves show mass loss,
# it is highly likely that the column represents the magnitude of loss rate or -dW/dT such that peaks are positive.
# OR, it could be raw derivative where some regions increase.
# Let's look at the "Onset" definition again.
# Standard ASTM E1131 onset: Draw tangent at inflection point (max slope).
# If the data provided is already the derivative, we use its value as the slope magnitude relative to the temperature axis direction.
# Usually, for mass loss, Weight decreases as Temp increases. So dW/dT < 0.
# If the plot has positive DTG peaks, it's likely plotted as -dW/dT or similar.
# However, mathematically:
# Tangent slope m_data = value in '미분중량' column.
# If m_data > 0, and Weight decreases, then actual dW/dT = -m_data? Or is Weight increasing?
# CNT production TGA: Residue remains. Mass loss occurs. Weight % should decrease from 100% to ~5%.
# So dW/dT is negative.
# If the column '미분중량' has positive max values (e.g., 2.04), it must represent -dW/dT (rate of loss).
# So the slope of the Weight vs Temp curve at the peak is NEGATIVE.
# Slope_actual = - peak_dtg_val.

slope_actual = -peak_dtg_val

# Now solve intersection with horizontal baseline at Y = baseline_weight
# Y_tangent = w_at_peak + slope_actual * (X - peak_temp)
# baseline_weight = w_at_peak + slope_actual * (T_onset - peak_temp)
# T_onset = peak_temp + (baseline_weight - w_at_peak) / slope_actual

if abs(slope_actual) < 1e-9:
    onset_temp = peak_temp # Fallback
else:
    onset_temp = peak_temp + (baseline_weight - w_at_peak) / slope_actual

# Create Plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot TG curve (Weight %)
color = 'tab:red'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('중량 (%)', color=color, fontsize=12)
ax1.plot(temps, weights, color=color, label='TG 곡선')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, linestyle='--', alpha=0.5)

# Plot DTG curve (Derivative Weight %) on secondary axis
ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('미분중량 (%/°C)', color=color2, fontsize=12)
ax2.plot(temps, dtgs, color=color2, label='DTG 곡선', alpha=0.7)
ax2.tick_params(axis='y', labelcolor=color2)

# Annotate Onset Temperature
# Draw the tangent line segment near the onset for visualization
t_start = onset_temp - 50
t_end = onset_temp + 50
w_start = w_at_peak + slope_actual * (t_start - peak_temp)
w_end = w_at_peak + slope_actual * (t_end - peak_temp)
ax1.plot([t_start, t_end], [w_start, w_end], 'k--', linewidth=1.5, label=f'Tangent @ Peak ({peak_temp:.1f}°C)')

# Draw baseline
ax1.axhline(y=baseline_weight, color='gray', linestyle=':', linewidth=1.5, label=f'Baseline ({baseline_weight:.1f}% @ 500°C)')

# Mark the onset point
ax1.scatter([onset_temp], [baseline_weight], color='black', zorder=5, s=50, marker='o')

# Text annotation
annotation_text = f'Extrapolated Onset: {onset_temp:.1f} °C'
ax1.annotate(annotation_text,
             xy=(onset_temp, baseline_weight),
             xytext=(onset_temp + 100, baseline_weight + 10),
             arrowprops=dict(facecolor='black', shrink=0.05),
             fontsize=12,
             bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.8))

# Add title and legend
ax1.set_title(f'{sheet_name} TGA Analysis', fontsize=14)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, f'{sheet_name}_tga_onset.png')
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
print(f"Calculated Extrapolated Onset Temperature: {onset_temp:.2f} °C")
