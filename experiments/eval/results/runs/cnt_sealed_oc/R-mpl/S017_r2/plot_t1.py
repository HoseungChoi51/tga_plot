import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"
sheet_name = "R2-260616-1"

# 1. Read Data
try:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
except Exception as e:
    raise ValueError(f"Could not read file {file_path} sheet {sheet_name}: {e}")

# Standardize column names based on preview: A 시간 (min), B 온도 (°C), C 중량 (%), D 미분중량 (%/°C)
# The headers might have extra spaces or be in Korean. We look for specific substrings.
cols = df.columns.tolist()
temp_col = next((c for c in cols if '온도' in str(c)), None)
weight_col = next((c for c in cols if '중량' in str(c) and '미분' not in str(c)), None)
dtg_col = next((c for c in cols if '미분' in str(c)), None)

if temp_col is None or weight_col is None or dtg_col is None:
    # Fallback to positional indices if header matching fails but data structure is known from preview
    # Preview says: A=Time, B=Temp, C=Weight, D=DTG. Index 1, 2, 3 respectively.
    temp_col = df.columns[1]
    weight_col = df.columns[2]
    dtg_col = df.columns[3]

# Extract columns
temperature = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Filter valid data points
valid_mask = ~np.isnan(temperature) & ~np.isnan(weight) & ~np.isnan(dtg)
T = temperature[valid_mask]
W = weight[valid_mask]
D = dtg[valid_mask]

# Sort by Temperature just in case
sort_idx = np.argsort(T)
T = T[sort_idx]
W = W[sort_idx]
D = D[sort_idx]

# 2. Calculate Extrapolated Onset Temperature
# Definition provided: 
# - Tangent at the steepest drop in the 450–800 °C range.
# - Baseline is the horizontal line of the weight at 500 °C.
# - Onset is where the tangent intersects the baseline.

# Step 2a: Find the maximum DTG peak in the range 450 <= T <= 800
mask_range = (T >= 450) & (T <= 800)
if not np.any(mask_range):
    raise ValueError("No data found in the 450-800 °C range.")

T_range = T[mask_range]
D_range = D[mask_range]

# Find index of max DTG (steepest drop). Note: DTG is negative for mass loss usually? 
# Let's check the preview: "미분중량 (%/°C) [수치 -0.01229~2.04224]". 
# Positive values here likely indicate derivative magnitude or sign convention difference. 
# Usually, TG curves decrease (negative slope). If D is positive, it might be absolute value or inverted.
# However, standard extrapolated onset uses the point of maximum *rate of change*.
# If D represents dW/dT, mass loss means dW < 0, so dW/dT < 0.
# The preview shows positive max values up to 2.04. This suggests the data might be |dW/dT| or -dW/dT.
# Or perhaps the reaction is gaining mass? Unlikely for CNT purification/TGA unless oxidation is being measured carefully or it's a specific step.
# Given "CNT production", TGA often measures purity (loss of amorphous carbon/metal catalysts) or oxidation stability.
# Let's assume the "steepest drop" corresponds to the extremum of the derivative curve in the specified window.
# If D is positive, we look for the Max D. If D were negative, we'd look for Min D (most negative).
# Based on preview max ~2.04, it's likely magnitude or -slope. We take the index of the MAXIMUM value in this window.

peak_idx_local = np.argmax(D_range)
peak_T = T_range[peak_idx_local]
peak_D = D_range[peak_idx_local]

# Step 2b: Determine the slope of the tangent at the peak.
# We can approximate the slope using local linear regression around the peak.
window_size = 10  # Number of points around the peak to fit a line
start_idx_global = np.searchsorted(T, peak_T)
idx_start = max(0, start_idx_global - window_size // 2)
idx_end = min(len(T), start_idx_global + window_size // 2 + 1)

T_fit = T[idx_start:idx_end]
W_fit = W[idx_start:idx_end]

# Fit a line: W = m*T + c
if len(T_fit) > 1:
    coeffs = np.polyfit(T_fit, W_fit, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
else:
    # Fallback if window too small
    slope = peak_D  # Approximate
    # Need a point on the line to find intercept relative to global coords
    # Using the actual weight at peak T
    w_at_peak = W[np.argmin(np.abs(T - peak_T))]
    intercept = w_at_peak - slope * peak_T

# Step 2c: Define the Baseline
# "Baseline is the horizontal line of the weight at 500 °C"
# Find weight closest to 500 °C
idx_500 = np.argmin(np.abs(T - 500))
baseline_weight = W[idx_500]

# Step 2d: Calculate Intersection (Extrapolated Onset)
# Line equation: W = slope * T + intercept
# Baseline equation: W = baseline_weight
# baseline_weight = slope * T_onset + intercept
# T_onset = (baseline_weight - intercept) / slope

if abs(slope) < 1e-9:
    T_onset = peak_T  # Avoid division by zero
else:
    T_onset = (baseline_weight - intercept) / slope
    
    # Sanity check: The onset should logically be before the peak in a decomposition process.
    # If the calculation yields something weird (e.g., far off), stick to the visual interpretation or fallback.
    # However, strictly following user instruction: tangent at max DTG, baseline at 500C weight.

# 3. Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

color_temp = 'tab:red'
ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Weight (%)', color=color_temp)
ax1.plot(T, W, color=color_temp, label='TG (Weight %)')
ax1.tick_params(axis='y', labelcolor=color_temp)
ax1.grid(True, linestyle='--', alpha=0.5)

ax2 = ax1.twinx()
color_dtg = 'tab:blue'
ax2.set_ylabel('Derivative Weight (%/°C)', color=color_dtg)
ax2.plot(T, D, color=color_dtg, label='DTG (Derivative %/°C)')
ax2.tick_params(axis='y', labelcolor=color_dtg)

# Highlight the 450-800 range used for selection
ax1.axvspan(450, 800, color='gray', alpha=0.1, label='Analysis Range (450-800°C)')

# Draw the tangent line segment near the peak for visualization
# Extend the tangent line slightly
tangent_x_start = max(450, peak_T - 50)
tangent_x_end = min(800, peak_T + 50)
tangent_y_start = slope * tangent_x_start + intercept
tangent_y_end = slope * tangent_x_end + intercept

ax1.plot([tangent_x_start, tangent_x_end], [tangent_y_start, tangent_y_end], 
         'g--', linewidth=1.5, label=f'Tangent @ Peak ({peak_T:.1f}°C)')

# Draw the baseline
ax1.axhline(baseline_weight, xmin=0, xmax=1, color='purple', linestyle=':', linewidth=1.5, label=f'Baseline @ 500°C ({baseline_weight:.2f}%)')

# Mark the Onset Point
ax1.plot(T_onset, baseline_weight, 'ko', markersize=8, zorder=5)
ax1.annotate(f'Onset: {T_onset:.1f} °C', 
             xy=(T_onset, baseline_weight), 
             xytext=(T_onset + 20, baseline_weight + 10),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=10, fontweight='bold', color='black',
             bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="k", lw=1, alpha=0.7))

# Title and Legend
ax1.set_title(f'TGA Analysis: Sheet "{sheet_name}"\nExtrapolated Onset Temperature Calculation')

# Combine legends
lines_labels = ax1.get_legend_handles_labels()
lines_labels2 = ax2.get_legend_handles_labels()
# Only use lines from ax1 mostly, but include all unique labels
legend_elements = lines_labels[0] + lines_labels2[0]
legend_labels = lines_labels[1] + lines_labels2[1]
ax1.legend(legend_elements, legend_labels, loc='best')

plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, f"TGA_{sheet_name.replace('/', '_')}_onset.png")
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
print(f"Calculated Onset Temperature: {T_onset:.2f} °C")
print(f"Peak DTG Temperature: {peak_T:.2f} °C")
print(f"Baseline Weight at 500°C: {baseline_weight:.2f} %")
