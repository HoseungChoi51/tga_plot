import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Configure Korean font support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B19_r2/out"

# Ensure output directory exists
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read the PVC sheet from the Excel file
df_pvc = pd.read_excel(DATA_FILE, sheet_name="PVC")

# Extract relevant columns based on standard TGA structure identified in preview
# Assuming columns: Time, Temperature, Weight, Deriv. Weight
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temperature = df_pvc[temp_col].values
weight = df_pvc[weight_col].values
dtg = df_pvc[dtg_col].values

# Filter data for 200°C to 400°C range to calculate mass loss
mask_200_400 = (temperature >= 200) & (temperature <= 400)
temps_range = temperature[mask_200_400]
weights_range = weight[mask_200_400]

if len(temps_range) > 0:
    # Find weight at ~200°C and ~400°C
    idx_200 = np.argmin(np.abs(temps_range - 200))
    idx_400 = np.argmin(np.abs(temps_range - 400))
    
    w_200 = weights_range[idx_200]
    w_400 = weights_range[idx_400]
    
    t_200 = temps_range[idx_200]
    t_400 = temps_range[idx_400]
    
    mass_loss = w_200 - w_400
else:
    mass_loss = 0
    t_200, t_400, w_200, w_400 = 200, 400, 0, 0

# Create the plot
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left axis (y1)
color_weight = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_weight, fontsize=12)
line1, = ax1.plot(temperature, weight, color=color_weight, linewidth=1.5, label='Weight')
ax1.tick_params(axis='y', labelcolor=color_weight)

# Plot DTG on right axis (y2), inverted so peaks point up
ax2 = ax1.twinx()
color_dtg = '#c0392b'
ax2.set_ylabel('DTG (%/°C)', color=color_dtg, fontsize=12)
# Multiply by -1 to make peaks positive/upward
line2, = ax2.plot(temperature, dtg * -1, color=color_dtg, linewidth=1.5, linestyle='--', label='DTG')
ax2.tick_params(axis='y', labelcolor=color_dtg)

# Title is the sheet name
plt.title("PVC", fontsize=14, pad=15)

# Calculate Residue at ~800°C
idx_residue = np.argmin(np.abs(temperature - 800))
residue_temp = temperature[idx_residue]
residue_weight = weight[idx_residue]

# Calculate Peak Temp (highest DTG peak above 150°C)
# We look for max of (-dtg) because dtg is negative during loss, so -dtg is positive peak height
mask_peak = temperature > 150
if np.any(mask_peak):
    dtg_positive = dtg * -1
    # Only consider where dtg_positive is actually positive (mass loss region)
    valid_peaks = dtg_positive[mask_peak]
    temps_valid = temperature[mask_peak]
    
    if len(valid_peaks) > 0:
        idx_max_peak = np.argmax(valid_peaks)
        peak_temp = temps_valid[idx_max_peak]
        peak_val = valid_peaks[idx_max_peak]
    else:
        peak_temp = None
        peak_val = None
else:
    peak_temp = None
    peak_val = None

# Add markers and labels for Residue and Peak
# Residue Marker
ax1.plot(residue_temp, residue_weight, 'o', color=color_weight, markersize=6)
ax1.annotate(f'Residue {residue_weight:.1f}%', 
             xy=(residue_temp, residue_weight), 
             xytext=(10, -15), textcoords='offset points',
             color=color_weight, fontsize=10,
             arrowprops=dict(arrowstyle='->', color=color_weight))

# Peak Marker
if peak_temp is not None:
    ax2.plot(peak_temp, peak_val, 'v', color=color_dtg, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_val), 
                 xytext=(10, 10), textcoords='offset points',
                 color=color_dtg, fontsize=10,
                 arrowprops=dict(arrowstyle='->', color=color_dtg))

# Display Mass Loss between 200 and 400 C
# Draw vertical lines or annotations to indicate the range
ax1.axvline(x=t_200, color='gray', linestyle=':', linewidth=1)
ax1.axvline(x=t_400, color='gray', linestyle=':', linewidth=1)

# Annotate the mass loss value
mid_t = (t_200 + t_400) / 2
mid_w = (w_200 + w_400) / 2
annotation_text = f'Mass Loss (200-400°C): {mass_loss:.2f}%'
ax1.text(mid_t, mid_w, annotation_text, 
         ha='center', va='bottom', fontsize=10, 
         bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

plt.tight_layout()

# Save figure
output_path = Path(OUT_DIR) / "PVC_mass_loss.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
