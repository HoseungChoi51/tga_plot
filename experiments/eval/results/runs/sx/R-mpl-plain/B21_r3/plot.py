import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B21_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the "Raw" sheet
df = pd.read_excel(DATA_FILE, sheet_name="Raw")

# Extract columns
temperature = df["Temperature (°C)"]
weight = df["Weight (%)"]
deriv_weight = df["Deriv. Weight (%/°C)"]

# Create figure with two subplots sharing x-axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

# Plot TGA curve (Weight %) on top subplot
ax1.plot(temperature, weight, color='blue', label='Weight (%)')
ax1.set_ylabel('Weight (%)')
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.5)

# Plot DTG curve (Deriv. Weight) on bottom subplot
ax2.plot(temperature, deriv_weight, color='red', label='Deriv. Weight (%/°C)')
ax2.set_xlabel('Temperature (°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)')
ax2.legend(loc='lower left')
ax2.grid(True, linestyle='--', alpha=0.5)

# Reverse x-axis so high temperature is on the left
ax1.invert_xaxis()
ax2.invert_xaxis()

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "tga_raw_reversed.png")
plt.savefig(output_path, dpi=300)
plt.close()
