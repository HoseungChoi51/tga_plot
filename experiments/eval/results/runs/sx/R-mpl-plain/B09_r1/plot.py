import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B09_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the PE sheet
df_pe = pd.read_excel(DATA_FILE, sheet_name="PE")

# Extract columns based on the preview info
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Deriv. Weight (%/°C)"

x = df_pe[x_col]
y1 = df_pe[y1_col]
y2 = df_pe[y2_col]

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot y1 (Weight %) with specific styling: bold (linewidth=3), red color
color_y1 = 'red'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
line1 = ax1.plot(x, y1, color=color_y1, linewidth=3, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color_y1)

# Set x-axis limits and ticks
ax1.set_xlim(100, 700)
ax1.set_xticks(np.arange(100, 701, 100))

# Create a second y-axis for Deriv. Weight
ax2 = ax1.twinx()
color_y2 = 'blue'
ax2.set_ylabel('Deriv. Weight (%/°C)', color=color_y2, fontsize=12)
line2 = ax2.plot(x, y2, color=color_y2, linewidth=1.5, linestyle='--', label='Deriv. Weight (%/°C)')
ax2.tick_params(axis='y', labelcolor=color_y2)

# Title
plt.title('TGA Data for PE', fontsize=14)

# Combine legends from both axes
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_path = os.path.join(OUT_DIR, "PE_tga_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
