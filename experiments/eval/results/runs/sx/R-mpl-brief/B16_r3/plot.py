import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B16_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read data
df = pd.read_csv(DATA_FILE)

# Identify columns based on preview
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Deriv. Weight (%/°C)"

x = df[x_col].values
y1 = df[y1_col].values
y2 = df[y2_col].values

# Prepare DTG for plotting: multiply by -1 so peaks point up
dtg_plot = y2 * -1

# Find residue at nearest 800 °C
idx_residue = np.argmin(np.abs(x - 800))
residue_val = y1[idx_residue]
residue_temp = x[idx_residue]

# Find peak temperature of highest DTG peak above 150 °C
mask_above_150 = x > 150
if np.any(mask_above_150):
    # dtg_plot is already inverted (-1 * original), so max value corresponds to deepest mass loss
    idx_peak_local = np.argmax(dtg_plot[mask_above_150])
    idx_peak = np.where(mask_above_150)[0][idx_peak_local]
    peak_temp = x[idx_peak]
else:
    # Fallback if no data above 150
    idx_peak = np.argmax(dtg_plot)
    peak_temp = x[idx_peak]

# Create figure with two subplots sharing x-axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

# Plot Weight (%) on top subplot
ax1.plot(x, y1, color='#1f4e9c', label='Weight (%)')
ax1.set_ylabel('Weight (%)')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend(loc='center left')

# Add residue marker and label on weight plot
ax1.scatter([residue_temp], [residue_val], color='black', zorder=5)
ax1.annotate(f'Residue {residue_val:.1f}%', 
             xy=(residue_temp, residue_val), 
             xytext=(10, 10), textcoords='offset points',
             fontsize=10, ha='left', va='bottom')

# Plot DTG on bottom subplot
ax2.plot(x, dtg_plot, color='#c0392b', label='DTG (%/°C)')
ax2.set_xlabel('Temperature (°C)')
ax2.set_ylabel('DTG (%/°C)')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend(loc='center left')

# Add peak marker and label on DTG plot
ax2.scatter([peak_temp], [dtg_plot[np.where(x == peak_temp)[0][0]]], color='black', zorder=5)
ax2.annotate(f'{peak_temp:.0f} °C', 
             xy=(peak_temp, dtg_plot[np.where(x == peak_temp)[0][0]]), 
             xytext=(10, 10), textcoords='offset points',
             fontsize=10, ha='left', va='bottom')

# Adjust layout
plt.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, "caox.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
