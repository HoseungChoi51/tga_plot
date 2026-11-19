import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B12_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_FILE)

# Identify columns based on the preview info
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"

# Filter data for x range 100 to 900
mask = (df[temp_col] >= 100) & (df[temp_col] <= 900)
df_plot = df[mask].copy()

if df_plot.empty:
    raise ValueError("No data found in the specified temperature range (100-900 °C)")

# Find residue at 900 °C
# We need the weight at the point nearest to 900 °C within the filtered or original data?
# The user asked to label residue at 900. Usually, this means finding the value at T=900.
# Let's find the index of the row closest to 900 °C in the original dataframe to be precise,
# but since we are plotting only 100-900, let's look in the plotted subset or original.
# It is safer to use the original data to find the exact point near 900 if it exists, 
# otherwise interpolate or take the closest available.
idx_900 = (df[temp_col] - 900).abs().idxmin()
residue_temp = df.loc[idx_900, temp_col]
residue_weight = df.loc[idx_900, weight_col]

# Create plot
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight curve
ax1.plot(df_plot[temp_col], df_plot[weight_col], color='#1f4e9c', linewidth=1.5, label='Weight (%)')

# Set axis labels and title
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax1.set_title('caox', fontsize=14)

# Set X axis range
ax1.set_xlim([100, 900])

# Add marker and label for residue at 900 °C
# Only add if the point is within the plot limits (it should be)
ax1.plot(residue_temp, residue_weight, 'o', color='black', markersize=6)
label_text = f'Residue {residue_weight:.1f}%'
ax1.annotate(label_text, xy=(residue_temp, residue_weight), xytext=(10, 10),
             textcoords='offset points', fontsize=10, ha='left', va='bottom',
             bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

# Grid
ax1.grid(True, linestyle='--', alpha=0.6)

# Legend
ax1.legend(loc='center left')

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "caox.png")
plt.savefig(output_path, dpi=300)
plt.close()
