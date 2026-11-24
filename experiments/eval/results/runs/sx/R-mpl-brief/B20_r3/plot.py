import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B20_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet
sheet_name = "Acid-washed"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Identify columns based on preview info
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Deriv. Weight (%/°C)"

temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Create figure and axis
fig, y1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
color_y1 = '#1f4e9c'
y1.plot(temp, weight, color=color_y1, label='Weight (%)')
y1.set_xlabel('Temperature (°C)', fontsize=12)
y1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
y1.tick_params(axis='y', labelcolor=color_y1)

# Add minor ticks to x-axis
y1.xaxis.set_minor_locator(AutoMinorLocator())
y1.tick_params(which='minor', direction='in', length=4)

# Create secondary y-axis for DTG
y2 = y1.twinx()
color_y2 = '#c0392b'
# Multiply DTG by -1 so peaks point up
dtg_inv = dtg * -1
y2.plot(temp, dtg_inv, color=color_y2, label='DTG (%/°C)')
y2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
y2.tick_params(axis='y', labelcolor=color_y2)

# Find Residue at ~800°C
idx_800 = np.argmin(np.abs(temp - 800))
residue_val = weight[idx_800]
residue_temp = temp[idx_800]

# Plot residue marker
y1.scatter(residue_temp, residue_val, color=color_y1, zorder=5, s=50)
y1.annotate(f'Residue {residue_val:.1f}%', 
            xy=(residue_temp, residue_val), 
            xytext=(residue_temp + 50, residue_val + 5),
            arrowprops=dict(facecolor='black', shrink=0.05),
            fontsize=10, color='black')

# Find Peak: highest DTG peak above 150°C
mask = temp > 150
if np.any(mask):
    # Find local maxima in dtg_inv within mask
    # Simple approach: find global max of dtg_inv where temp > 150
    dtg_inv_masked = dtg_inv[mask]
    temp_masked = temp[mask]
    
    idx_peak_local = np.argmax(dtg_inv_masked)
    peak_temp = temp_masked[idx_peak_local]
    peak_dtg_inv_val = dtg_inv_masked[idx_peak_local]
    
    # Plot peak marker on right axis (using original negative DTG or inverted? 
    # The prompt says DTG multiplied by -1. So we plot dtg_inv. 
    # The marker should be on the curve plotted on y2.
    y2.scatter(peak_temp, peak_dtg_inv_val, color=color_y2, zorder=5, s=50)
    y2.annotate(f'{peak_temp:.0f} °C', 
                xy=(peak_temp, peak_dtg_inv_val), 
                xytext=(peak_temp + 50, peak_dtg_inv_val - 0.2),
                arrowprops=dict(facecolor='black', shrink=0.05),
                fontsize=10, color='black')

# Title
y1.set_title(sheet_name, fontsize=14)

# Legend
lines1, labels1 = y1.get_legend_handles_labels()
lines2, labels2 = y2.get_legend_handles_labels()
y1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

# Grid
y1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

# Save
out_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
plt.savefig(out_path, dpi=300)
plt.close()
