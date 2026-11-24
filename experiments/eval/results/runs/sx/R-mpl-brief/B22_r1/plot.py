import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B22_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet "Raw"
df = pd.read_excel(DATA_FILE, sheet_name="Raw")

# Extract columns based on the preview
time_col = "Time (min)"
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temp = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Find the weight at 150 °C for normalization
idx_150 = np.argmin(np.abs(temp - 150))
weight_at_150 = weight[idx_150]

# Normalize weight so that it is 100% at 150 °C
if weight_at_150 != 0:
    weight_norm = (weight / weight_at_150) * 100.0
else:
    weight_norm = weight.copy() # Fallback if division by zero occurs, though unlikely here

# Prepare data for plotting
# DTG needs to be inverted (-1 * dtg) so peaks point up
dtg_plot = -1 * dtg

# Create figure and axes
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
line1 = ax1.plot(temp, weight_norm, color='#1f4e9c', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f4e9c')

# Plot DTG on right y-axis
ax2 = ax1.twinx()
line2 = ax2.plot(temp, dtg_plot, color='#c0392b', label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#c0392b')

# Title
sheet_name = "Raw"
ax1.set_title(sheet_name, fontsize=14)

# Calculate Residue at 800 °C
idx_800 = np.argmin(np.abs(temp - 800))
residue_val = weight_norm[idx_800]
residue_temp = temp[idx_800]

# Add residue marker and text
ax1.scatter(residue_temp, residue_val, color='#1f4e9c', zorder=5)
ax1.annotate(f'Residue {residue_val:.1f}%', 
             xy=(residue_temp, residue_val), 
             xytext=(residue_temp + 50, residue_val + 10),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=10, color='#1f4e9c')

# Calculate Peak temperature above 150 °C
mask_peak = temp > 150
if np.any(mask_peak):
    # Find index of maximum DTG value in the masked region
    max_dtg_idx = np.argmax(dtg_plot[mask_peak])
    peak_temp = temp[mask_peak][max_dtg_idx]
    peak_dtg_val = dtg_plot[mask_peak][max_dtg_idx]
    
    # Add peak marker and text
    ax2.scatter(peak_temp, peak_dtg_val, color='#c0392b', zorder=5)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_dtg_val), 
                 xytext=(peak_temp + 50, peak_dtg_val + 0.1),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color='#c0392b')

# Legend
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5))

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

# Save plot
output_path = os.path.join(OUT_DIR, f"{sheet_name}_normalized.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
