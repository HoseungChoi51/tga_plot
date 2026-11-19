import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B03_r2/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
df = pd.read_csv(DATA_FILE)

# Extract columns based on the preview info
# Column A: Angular frequency (rad/s) -> x-axis
# Column B: Storage modulus G' (Pa) -> Left y-axis (y1)
# Column C: Loss modulus G'' (Pa) -> Right y-axis (y2)

col_x = df.columns[0] # Angular frequency
col_y1 = df.columns[1] # Storage modulus G'
col_y2 = df.columns[2] # Loss modulus G''

x = df[col_x].values
y1 = df[col_y1].values
y2 = df[col_y2].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot G' on left axis
color1 = '#1f4e9c'
ax1.plot(x, y1, color=color1, label="G' (Storage Modulus)", linewidth=2)
ax1.set_xlabel('Angular Frequency (rad/s)', fontsize=12)
ax1.set_ylabel("G' (Pa)", color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Set log scale for x and y1
ax1.set_xscale('log')
ax1.set_yscale('log')

# Create second axis sharing x
ax2 = ax1.twinx()

# Plot G'' on right axis
color2 = '#c0392b'
ax2.plot(x, y2, color=color2, label="G'' (Loss Modulus)", linewidth=2, linestyle='--')
ax2.set_ylabel("G'' (Pa)", color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Set log scale for y2
ax2.set_yscale('log')

# Title
plt.title('Rheological Properties vs Angular Frequency', fontsize=14)

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')

# Grid
ax1.grid(True, which="both", ls="-", alpha=0.3)

# Adjust layout to prevent label clipping
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "rheology_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
