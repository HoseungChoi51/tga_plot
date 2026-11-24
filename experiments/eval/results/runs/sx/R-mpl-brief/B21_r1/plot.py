import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B21_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

sheet_name = "Raw"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# Identify columns based on preview info
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Deriv. Weight (%/°C)"

temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
color1 = '#1f4e9c'
ax1.plot(temp, weight, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Invert x-axis to make high temperature on the left
ax1.invert_xaxis()

# Create secondary y-axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
# Multiply DTG by -1 so peaks point up
ax2.plot(temp, -dtg, color=color2, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Find Residue at ~800°C
idx_800 = np.argmin(np.abs(temp - 800))
residue_val = weight[idx_800]
residue_temp = temp[idx_800]

# Add residue marker and text
ax1.scatter(residue_temp, residue_val, color=color1, zorder=5, s=50)
ax1.text(residue_temp, residue_val + 2, f'Residue {residue_val:.1f}%', 
         color=color1, ha='center', va='bottom', fontsize=10, fontweight='bold')

# Find Peak in DTG above 150°C
mask_above_150 = temp > 150
if np.any(mask_above_150):
    dtg_above_150 = dtg[mask_above_150]
    temp_above_150 = temp[mask_above_150]
    
    # Since we plot -dtg, the highest peak corresponds to the most negative dtg value
    idx_peak = np.argmin(dtg_above_150)
    peak_temp = temp_above_150[idx_peak]
    peak_dtg_val = dtg_above_150[idx_peak]
    
    # Plot marker on the inverted DTG curve (which is -peak_dtg_val)
    ax2.scatter(peak_temp, -peak_dtg_val, color=color2, zorder=5, s=50)
    ax2.text(peak_temp, -peak_dtg_val + abs(min(-dtg))*0.05, f'{peak_temp:.0f} °C', 
             color=color2, ha='center', va='bottom', fontsize=10, fontweight='bold')

# Title
ax1.set_title(sheet_name, fontsize=14, fontweight='bold')

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')

# Adjust layout
fig.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
plt.savefig(out_path, dpi=300)
plt.close()
