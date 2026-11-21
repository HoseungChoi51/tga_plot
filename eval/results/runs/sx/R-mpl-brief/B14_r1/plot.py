import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B14_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read the PVC sheet
df = pd.read_excel(DATA_FILE, sheet_name='PVC')

# Extract columns based on standard TGA structure identified in preview
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
dtg_col = 'Deriv. Weight (%/°C)'

temperature = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 7))

# Plot Weight (%) on left y-axis
color_weight = '#1f4e9c'
ax1.plot(temperature, weight, color=color_weight, linewidth=2, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=16)
ax1.set_ylabel('Weight (%)', color=color_weight, fontsize=16)
ax1.tick_params(axis='y', labelcolor=color_weight, labelsize=14)
ax1.tick_params(axis='x', labelsize=14)

# Create second y-axis for DTG
ax2 = ax1.twinx()
color_dtg = '#c0392b'
# Multiply DTG by -1 so peaks point up
ax2.plot(temperature, -dtg, color=color_dtg, linewidth=2, linestyle='--', label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color_dtg, fontsize=16)
ax2.tick_params(axis='y', labelcolor=color_dtg, labelsize=14)

# Title
sheet_name = 'PVC'
plt.title(sheet_name, fontsize=18, fontweight='bold')

# Find Residue at ~800°C
idx_800 = np.argmin(np.abs(temperature - 800))
residue_val = weight[idx_800]
residue_temp = temperature[idx_800]
ax1.plot(residue_temp, residue_val, 'o', color=color_weight, markersize=8)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val),
             xytext=(10, -15), textcoords='offset points',
             fontsize=14, color=color_weight, ha='left')

# Find Peak above 150°C
mask_above_150 = temperature > 150
if np.any(mask_above_150):
    dtg_masked = dtg[mask_above_150]
    temp_masked = temperature[mask_above_150]
    # Find index of minimum DTG (which corresponds to maximum mass loss rate)
    idx_min_dtg = np.argmin(dtg_masked)
    peak_temp = temp_masked[idx_min_dtg]
    peak_dtg_val = dtg_masked[idx_min_dtg]
    
    # Plot marker on DTG curve (note: we plot -dtg, so use -peak_dtg_val for y position on ax2)
    ax2.plot(peak_temp, -peak_dtg_val, 'v', color=color_dtg, markersize=10)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, -peak_dtg_val),
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=14, color=color_dtg, ha='left')

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=14)

# Grid
ax1.grid(True, linestyle=':', alpha=0.6)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, f"{sheet_name}_TGA.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
