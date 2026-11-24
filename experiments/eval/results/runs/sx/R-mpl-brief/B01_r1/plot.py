import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Load data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B01_r1/out"

df = pd.read_csv(DATA_FILE)

# Extract columns based on preview
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temps = df[temp_col].values
weights = df[weight_col].values
dtgs = df[dtg_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot TGA curve (left y-axis)
ax1.plot(temps, weights, color='#1f4e9c', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f4e9c')

# Plot DTG curve (right y-axis), multiplied by -1 so peaks point up
ax2 = ax1.twinx()
ax2.plot(temps, dtgs * -1, color='#c0392b', label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#c0392b')

# Define regions to shade
regions = [
    {'start': 120, 'end': 250, 'label': 'H₂O', 'color': '#FFB3BA'},
    {'start': 430, 'end': 580, 'label': 'CO', 'color': '#BAFFC9'},
    {'start': 640, 'end': 830, 'label': 'CO₂', 'color': '#BAE1FF'}
]

for region in regions:
    start = region['start']
    end = region['end']
    label = region['label']
    color = region['color']
    
    # Shade the region on the plot
    ax1.axvspan(start, end, alpha=0.3, color=color)
    
    # Add text label above the shaded region
    # Find a reasonable y position for the text (top of the plot area)
    y_pos = ax1.get_ylim()[1] * 0.95
    x_mid = (start + end) / 2
    ax1.text(x_mid, y_pos, label, ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')

# Title
ax1.set_title('TGA Analysis with Decomposition Regions', fontsize=14)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

# Adjust layout
plt.tight_layout()

# Save figure
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, 'caox_regions.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
