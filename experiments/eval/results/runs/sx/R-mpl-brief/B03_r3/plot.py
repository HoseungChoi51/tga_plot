import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Load data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/rheology.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B03_r3/out"

df = pd.read_csv(DATA_FILE)

# Extract columns based on the preview
x_col = "Angular frequency (rad/s)"
y1_col = "Storage modulus G' (Pa)"
y2_col = "Loss modulus G'' (Pa)"

x_data = df[x_col].values
y1_data = df[y1_col].values
y2_data = df[y2_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot G' on left y-axis
color1 = '#1f4e9c'
ax1.plot(x_data, y1_data, color=color1, label="G'", linewidth=2)
ax1.set_xlabel("Angular Frequency (rad/s)", fontsize=12)
ax1.set_ylabel("Storage Modulus G' (Pa)", color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xscale('log')
ax1.set_yscale('log')

# Create second y-axis for G''
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(x_data, y2_data, color=color2, label="G''", linewidth=2)
ax2.set_ylabel("Loss Modulus G'' (Pa)", color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_yscale('log')

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

# Title
plt.title("Rheology Data: Moduli vs Angular Frequency")

# Adjust layout to prevent overlap
fig.tight_layout()

# Save figure
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "rheology_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
