import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure font for Korean text
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/04_r2/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Sheet name specified by user
sheet_name = "1006R1-V normal"

# Read data
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Identify columns based on standard TGA structure or guess from preview
# Columns: Time, Temperature, Weight(%), D.W(%/C)
col_x = 'Temperature'
col_y1 = 'Weight(%)'
col_y2 = 'D.W(%/C)'

# Extract data
temp = df[col_x].values
weight = df[col_y1].values
dtg = df[col_y2].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis (y1)
color_y1 = '#1f4e9c'
ax1.plot(temp, weight, color=color_y1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_y1)

# Plot DTG on right y-axis (y2), multiplied by -1 to make peaks point up
ax2 = ax1.twinx()
color_y2 = '#c0392b'
dtg_inv = dtg * -1
ax2.plot(temp, dtg_inv, color=color_y2, label='DTG (-dW/dT)')
ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color_y2)

# Title customization
title_text = 'CNT 산화 거동'
title_color = 'navy' # 남색
title_size = 18
ax1.set_title(title_text, fontsize=title_size, color=title_color)

# Find Residue at nearest 800°C
idx_800 = np.argmin(np.abs(temp - 800))
residue_temp = temp[idx_800]
residue_weight = weight[idx_800]
residue_label = f'Residue {residue_weight:.1f}%'

# Mark residue on the plot
ax1.plot(residue_temp, residue_weight, 'o', color=color_y1, markersize=5)
ax1.annotate(residue_label, 
             xy=(residue_temp, residue_weight), 
             xytext=(residue_temp + 20, residue_weight + 5),
             arrowprops=dict(facecolor=color_y1, shrink=0.05, width=1, headwidth=5),
             fontsize=10, color=color_y1)

# Find Peak temperature of highest DTG peak above 150°C
# We look for the maximum of the inverted DTG (which corresponds to the most negative original DTG)
mask_above_150 = temp > 150
if np.any(mask_above_150):
    dtg_inv_filtered = dtg_inv[mask_above_150]
    temp_filtered = temp[mask_above_150]
    
    idx_peak_local = np.argmax(dtg_inv_filtered)
    peak_temp = temp_filtered[idx_peak_local]
    peak_dtg_val = dtg_inv_filtered[idx_peak_local]
    
    # Get corresponding weight at peak temp for marker placement if needed, but usually marker is on DTG curve
    # The prompt says "marker on the curve". For peak, it's typically on the DTG curve.
    
    peak_label = f'{peak_temp:.0f} °C'
    
    # Mark peak on the DTG curve (ax2)
    ax2.plot(peak_temp, peak_dtg_val, 'o', color=color_y2, markersize=5)
    ax2.annotate(peak_label, 
                 xy=(peak_temp, peak_dtg_val), 
                 xytext=(peak_temp + 20, peak_dtg_val + 0.1),
                 arrowprops=dict(facecolor=color_y2, shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color=color_y2)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.05, 0.5))

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, f"{sheet_name.replace(' ', '_')}.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
