import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Read data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B01_r2/out"

df = pd.read_csv(DATA_FILE)

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values

# Define regions and labels
regions = [
    (120, 250, 'H2O', '#FF9999'),   # Light red
    (430, 580, 'CO', '#99CCFF'),     # Light blue
    (640, 830, 'CO2', '#99FF99')     # Light green
]

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Plot TGA curve
ax.plot(temp, weight, color='black', linewidth=1.5, label='TGA')

# Add shaded regions and annotations
for start, end, label, color in regions:
    ax.axvspan(start, end, alpha=0.3, color=color, label=label)
    # Place text at the center of each region, near the top
    mid_temp = (start + end) / 2
    # Find y position: use a fixed high value or interpolate
    # We'll place it above the curve slightly, using max weight in that range minus some offset
    mask = (temp >= start) & (temp <= end)
    if np.any(mask):
        y_pos = np.max(weight[mask]) + 2  # Slightly above the max weight in the region
    else:
        y_pos = 100
    
    ax.text(mid_temp, y_pos, label, ha='center', va='bottom', fontsize=12, fontweight='bold')

# Labels and title
ax.set_xlabel('Temperature (°C)', fontsize=12)
ax.set_ylabel('Weight (%)', fontsize=12)
ax.set_title('TGA Curve with Decomposition Regions', fontsize=14)
ax.legend(loc='lower left', fontsize=10)

# Set axis limits to focus on relevant temperature range
ax.set_xlim(0, 950)
ax.set_ylim(30, 105)

# Grid
ax.grid(True, linestyle='--', alpha=0.5)

# Save plot
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "tga_regions.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
