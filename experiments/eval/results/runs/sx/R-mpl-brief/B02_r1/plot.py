import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B02_r1/out"

# Read data
df = pd.read_csv(DATA_FILE)

# Extract columns
temp = df["Temperature (°C)"].values
weight = df["Weight (%)"].values
heat_flow = df["Heat Flow (W/g)"].values

# Create figure and axes
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight on left y-axis (y1)
color1 = '#1f4e9c'
ax1.plot(temp, weight, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Create right y-axis for Heat Flow
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(temp, heat_flow, color=color2, label='Heat Flow (W/g)')
ax2.set_ylabel('Heat Flow (W/g)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Find peaks in Heat Flow
# Endothermic peaks: positive values (absorbing heat)
# Exothermic peaks: negative values (releasing heat)

# For endothermic peaks (positive), we look for local maxima
endothermic_indices, _ = find_peaks(heat_flow, height=0.1, distance=50)
endothermic_temps = temp[endothermic_indices]
endothermic_values = heat_flow[endothermic_indices]

# For exothermic peaks (negative), we look for local minima (which are peaks in magnitude)
exothermic_indices, _ = find_peaks(-heat_flow, height=0.1, distance=50)
exothermic_temps = temp[exothermic_indices]
exothermic_values = heat_flow[exothermic_indices]

# Sort by temperature to ensure consistent ordering
if len(endothermic_temps) > 0:
    sort_idx = np.argsort(endothermic_temps)
    endothermic_temps = endothermic_temps[sort_idx]
    endothermic_values = endothermic_values[sort_idx]

if len(exothermic_temps) > 0:
    sort_idx = np.argsort(exothermic_temps)
    exothermic_temps = exothermic_temps[sort_idx]
    exothermic_values = exothermic_values[sort_idx]

# Mark the first two endothermic peaks and one exothermic peak
# If there are more than needed, take the first ones by temperature order
selected_endo_temps = endothermic_temps[:2] if len(endothermic_temps) >= 2 else endothermic_temps
selected_exo_temps = exothermic_temps[:1] if len(exothermic_temps) >= 1 else exothermic_temps

# Plot markers and labels for selected peaks
for i, t in enumerate(selected_endo_temps):
    # Find the corresponding heat flow value at this temperature
    idx = np.argmin(np.abs(temp - t))
    hf_val = heat_flow[idx]
    ax2.plot(t, hf_val, 'o', color='#27ae60', markersize=8, zorder=5)
    ax2.annotate(f'{t:.0f} °C\n(Endo)', xy=(t, hf_val), xytext=(t + 20, hf_val + 0.3),
                 fontsize=9, color='#27ae60', ha='left', va='bottom')

for i, t in enumerate(selected_exo_temps):
    idx = np.argmin(np.abs(temp - t))
    hf_val = heat_flow[idx]
    ax2.plot(t, hf_val, 's', color='#e67e22', markersize=8, zorder=5)
    ax2.annotate(f'{t:.0f} °C\n(Exo)', xy=(t, hf_val), xytext=(t + 20, hf_val - 0.5),
                 fontsize=9, color='#e67e22', ha='left', va='top')

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)

# Title
ax1.set_title("TGA/DSC Analysis", fontsize=14)

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

# Save figure
import os
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, "caox_heatflow.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
