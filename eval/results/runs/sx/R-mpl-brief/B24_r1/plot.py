import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B24_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the PE sheet
df = pd.read_excel(DATA_FILE, sheet_name="PE")

# Extract columns
temp_c = df["Temperature (°C)"].values
weight = df["Weight (%)"].values
dtg = df["Deriv. Weight (%/°C)"].values

# Convert temperature from Celsius to Kelvin
temp_k = temp_c + 273.15

# Create figure and axes
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight on left y-axis
color_weight = '#1f4e9c'
ax1.plot(temp_k, weight, color=color_weight, linewidth=1.5, label='Weight (%)')
ax1.set_xlabel('Temperature (K)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_weight, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_weight)

# Create second y-axis for DTG
ax2 = ax1.twinx()
color_dtg = '#c0392b'
# Multiply DTG by -1 so peaks point up
ax2.plot(temp_k, dtg * -1, color=color_dtg, linewidth=1.5, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color_dtg, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color_dtg)

# Find residue at nearest 800 °C (which is 1073.15 K)
target_temp_k = 800 + 273.15
idx_residue = np.argmin(np.abs(temp_k - target_temp_k))
residue_val = weight[idx_residue]
residue_temp_k = temp_k[idx_residue]

# Find peak: highest DTG peak above 150 °C (i.e., above 423.15 K)
target_min_temp_k = 150 + 273.15
mask = temp_k > target_min_temp_k
if mask.any():
    dtg_neg = dtg * -1
    dtg_masked = dtg_neg[mask]
    temp_masked = temp_k[mask]
    idx_peak_local = np.argmax(dtg_masked)
    peak_temp_k = temp_masked[idx_peak_local]
    peak_dtg_val = dtg_masked[idx_peak_local]
else:
    peak_temp_k = None
    peak_dtg_val = None

# Add markers and labels for residue
ax1.plot(residue_temp_k, residue_val, 'o', color=color_weight, markersize=8)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp_k, residue_val),
             xytext=(10, -15), textcoords='offset points',
             fontsize=10, color=color_weight,
             arrowprops=dict(arrowstyle='->', color=color_weight))

# Add markers and labels for peak
if peak_temp_k is not None:
    # For annotation on ax2, we need to convert back to original scale or use ax2 coords
    # Since we plotted dtg*-1, the value at peak is peak_dtg_val
    ax2.plot(peak_temp_k, peak_dtg_val, 'o', color=color_dtg, markersize=8)
    ax2.annotate(f'{peak_temp_k:.0f} K', xy=(peak_temp_k, peak_dtg_val),
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=10, color=color_dtg,
                 arrowprops=dict(arrowstyle='->', color=color_dtg))

# Title
ax1.set_title('PE', fontsize=14, fontweight='bold')

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.02, 0.5))

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "PE_K.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
