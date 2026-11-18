import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/04_r1/out"
SHEET_NAME = "1006R1-V normal"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet
df = pd.read_excel(DATA_FILE, sheet_name=SHEET_NAME, header=0)

# Identify columns based on the preview and standard TGA structure
# B: Temperature, C: Weight(%), D: D.W(%/C)
x_col = 'Temperature'
y1_col = 'Weight(%)'
y2_col = 'D.W(%/C)'

# Extract data
temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Prepare DTG for plotting (multiply by -1 so peaks point up)
dtg_plot = dtg * -1

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
color1 = '#1f4e9c'
ax1.plot(temp, weight, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Create secondary y-axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(temp, dtg_plot, color=color2, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Title settings
title_text = 'CNT 산화 거동'
ax1.set_title(title_text, fontsize=18, color='navy')

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')

# Calculate Residue at nearest 800 °C
# Find index of temperature closest to 800
idx_residue = np.argmin(np.abs(temp - 800))
residue_val = weight[idx_residue]
residue_temp = temp[idx_residue]

# Add residue marker and label
ax1.scatter(residue_temp, residue_val, color=color1, zorder=5)
ax1.annotate(f'Residue {residue_val:.1f}%', 
             xy=(residue_temp, residue_val), 
             xytext=(10, -10), textcoords='offset points',
             color=color1, fontsize=10, ha='left', va='top')

# Calculate Peak temperature (highest DTG peak above 150 °C)
# Filter data where temp > 150
mask = temp > 150
if np.any(mask):
    # We want the highest peak in the plotted DTG (which is -dtg). 
    # Since we plotted -dtg, the maximum value corresponds to the most negative original DTG (largest mass loss rate).
    # However, usually "peak" refers to the max magnitude of mass loss.
    # Let's find the index of the maximum value in dtg_plot (which is positive for mass loss) within the mask.
    dtg_filtered = dtg_plot[mask]
    temp_filtered = temp[mask]
    
    idx_peak_local = np.argmax(dtg_filtered)
    peak_temp = temp_filtered[idx_peak_local]
    peak_dtg_val = dtg_filtered[idx_peak_local]
    
    # Map back to original indices if needed, but we have the values directly from filtered arrays
    # Actually, let's just use the filtered arrays for annotation position
    peak_weight_val = weight[mask][idx_peak_local]
    
    # Add peak marker on the DTG curve (right axis)
    ax2.scatter(peak_temp, peak_dtg_val, color=color2, zorder=5)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_dtg_val), 
                 xytext=(10, 10), textcoords='offset points',
                 color=color2, fontsize=10, ha='left', va='bottom')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save figure
output_filename = f"{SHEET_NAME.replace(' ', '_')}.png"
output_path = os.path.join(OUT_DIR, output_filename)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
