import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B18_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the Annealed sheet
df = pd.read_excel(DATA_FILE, sheet_name='Annealed')

# Extract relevant columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
deriv_weight = df['Deriv. Weight (%/°C)'].values

# Find onset temperature using extrapolation method
# The onset temperature is typically found by drawing a tangent at the inflection point
# and extrapolating it to the baseline.

# First, find the inflection point (maximum derivative value in magnitude)
# Since weight decreases, derivative is negative. We look for the most negative value.
idx_max_deriv = np.argmin(deriv_weight)  # Most negative derivative
T_inflection = temp[idx_max_deriv]

# To find the onset, we need to draw a tangent line at the inflection point
# and find where it intersects with the initial baseline.

# Get points around the inflection point for linear fit
window_size = 50
start_idx = max(0, idx_max_deriv - window_size // 2)
end_idx = min(len(temp), idx_max_deriv + window_size // 2)

T_window = temp[start_idx:end_idx]
W_window = weight[start_idx:end_idx]

# Fit a linear regression to get the tangent slope
if len(T_window) > 1:
    coeffs = np.polyfit(T_window, W_window, 1)
    slope, intercept = coeffs[0], coeffs[1]
    
    # Define the baseline region (initial stable part before significant weight loss)
    # Typically first 5% of data or until temperature reaches ~100°C
    baseline_mask = temp < 100
    if np.sum(baseline_mask) > 10:
        T_baseline = temp[baseline_mask]
        W_baseline = weight[baseline_mask]
        baseline_slope, baseline_intercept = np.polyfit(T_baseline, W_baseline, 1)
        
        # Onset temperature is where the tangent line intersects the baseline
        # Tangent line: W = slope * T + intercept
        # Baseline: W = baseline_slope * T + baseline_intercept
        # Intersection: slope * T_onset + intercept = baseline_slope * T_onset + baseline_intercept
        if abs(slope - baseline_slope) > 1e-10:
            T_onset = (baseline_intercept - intercept) / (slope - baseline_slope)
        else:
            T_onset = T_inflection
    else:
        # If not enough baseline data, use a simple approach
        # Extrapolate from inflection point backwards
        T_onset = T_inflection - 50  # Rough estimate
else:
    T_onset = T_inflection

# Ensure T_onset is within reasonable range
T_onset = np.clip(T_onset, temp.min(), temp.max())

# Create figure with two subplots (TGA and DTG)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot TGA curve
ax1.plot(temp, weight, color='blue', linewidth=1.5, label='Weight (%)')
ax1.set_ylabel('Weight (%)', fontsize=12)
ax1.set_title('TGA/DTG Curve - Annealed', fontsize=14)
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(loc='upper right')

# Mark onset temperature on TGA plot
ax1.axvline(x=T_onset, color='red', linestyle='--', linewidth=1.5, label=f'Onset Temp: {T_onset:.1f}°C')
ax1.annotate(f'Onset: {T_onset:.1f}°C', 
             xy=(T_onset, np.interp(T_onset, temp, weight)),
             xytext=(T_onset + 50, np.interp(T_onset, temp, weight) + 10),
             arrowprops=dict(arrowstyle='->', color='red'),
             fontsize=10, color='red')

# Draw tangent line for visualization
T_tangent_start = max(temp.min(), T_onset - 30)
T_tangent_end = min(temp.max(), T_inflection + 30)
T_tangent = np.linspace(T_tangent_start, T_tangent_end, 100)
W_tangent = slope * T_tangent + intercept
ax1.plot(T_tangent, W_tangent, color='green', linestyle=':', linewidth=1.5, label='Tangent at inflection')

# Plot DTG curve
ax2.plot(temp, deriv_weight, color='orange', linewidth=1.5, label='Deriv. Weight (%/°C)')
ax2.set_xlabel('Temperature (°C)', fontsize=12)
ax2.set_ylabel('Deriv. Weight (%/°C)', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(loc='lower left')

# Mark inflection point on DTG plot
ax2.axvline(x=T_inflection, color='purple', linestyle='--', linewidth=1.5, label=f'Inflection: {T_inflection:.1f}°C')
ax2.annotate(f'Inflection: {T_inflection:.1f}°C',
             xy=(T_inflection, deriv_weight[idx_max_deriv]),
             xytext=(T_inflection + 50, deriv_weight[idx_max_deriv] - 0.1),
             arrowprops=dict(arrowstyle='->', color='purple'),
             fontsize=10, color='purple')

# Mark onset temperature on DTG plot as well
ax2.axvline(x=T_onset, color='red', linestyle='--', linewidth=1.5)

plt.tight_layout()

# Save the figure
output_path = os.path.join(OUT_DIR, "annealed_tga_onset.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Figure saved to: {output_path}")
print(f"Onset Temperature: {T_onset:.2f} °C")
print(f"Inflection Temperature: {T_inflection:.2f} °C")
