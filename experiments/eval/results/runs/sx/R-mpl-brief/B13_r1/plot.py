import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configure font for Korean support
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B13_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the PVC sheet
df = pd.read_excel(DATA_FILE, sheet_name='PVC')

# Extract columns based on preview info
temp_col = 'Temperature (°C)'
weight_col = 'Weight (%)'
dtg_col = 'Deriv. Weight (%/°C)'

temp = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight on left y-axis
color_weight = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_weight, fontsize=12)
line1, = ax1.plot(temp, weight, color=color_weight, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color_weight)

# Create second y-axis for DTG
ax2 = ax1.twinx()
color_dtg = '#c0392b'
ax2.set_ylabel('DTG (%/°C)', color=color_dtg, fontsize=12)
# Multiply DTG by -1 so peaks point up
line2, = ax2.plot(temp, dtg * -1, color=color_dtg, linestyle='--', label='DTG (%/°C)')
ax2.tick_params(axis='y', labelcolor=color_dtg)

# Title
ax1.set_title('PVC', fontsize=14)

# Find the two major DTG peaks above 150°C
# We look for local maxima in the inverted DTG curve (which corresponds to minima in original DTG)
dtg_inv = dtg * -1
mask = temp > 150

if np.any(mask):
    temps_masked = temp[mask]
    dtg_inv_masked = dtg_inv[mask]
    
    # Identify peaks: points that are greater than their neighbors
    # Using a simple peak detection logic
    peaks_indices = []
    for i in range(1, len(dtg_inv_masked) - 1):
        if dtg_inv_masked[i] > dtg_inv_masked[i-1] and dtg_inv_masked[i] > dtg_inv_masked[i+1]:
            # Filter out noise by requiring a certain prominence or just taking the highest ones
            # Since we want the "two places where weight drops sharply", these correspond to the highest DTG peaks.
            peaks_indices.append(i)
            
    if peaks_indices:
        # Get the values of the peaks found
        peak_vals = dtg_inv_masked[peaks_indices]
        
        # Sort indices by peak value descending to get the most significant ones
        sorted_indices = np.argsort(peak_vals)[::-1]
        
        # We want the top 2 distinct peaks. 
        # To ensure they are distinct, we can check distance or just take top 2 if they are far apart.
        # Given typical polymer degradation, PE/PVC/PET have clear main steps.
        
        selected_peaks_temps = []
        selected_peaks_weights = []
        
        # Helper to find nearest index in original array
        def get_nearest_idx(arr, val):
            return np.argmin(np.abs(arr - val))
        
        count = 0
        for idx in sorted_indices:
            current_peak_temp = temps_masked[idx]
            
            # Check if this peak is too close to already selected peaks (to avoid picking shoulders/noise near main peak)
            is_close = False
            for sel_t in selected_peaks_temps:
                if abs(current_peak_temp - sel_t) < 50: # Minimum separation of 50 degrees
                    is_close = True
                    break
            
            if not is_close:
                selected_peaks_temps.append(current_peak_temp)
                # Find corresponding weight at this temperature
                orig_idx = get_nearest_idx(temp, current_peak_temp)
                selected_peaks_weights.append(weight[orig_idx])
                count += 1
                
            if count >= 2:
                break
        
        # Annotate the peaks
        for p_t, p_w in zip(selected_peaks_temps, selected_peaks_weights):
            # Marker on DTG curve (using ax2)
            ax2.scatter(p_t, dtg_inv[get_nearest_idx(temp, p_t)], color=color_dtg, zorder=5, s=50)
            # Text annotation
            ax2.annotate(f'{p_t:.0f} °C', 
                         xy=(p_t, dtg_inv[get_nearest_idx(temp, p_t)]), 
                         xytext=(p_t + 20, dtg_inv[get_nearest_idx(temp, p_t)] + 0.2),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                         fontsize=10, color='black', ha='left')

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.02, 0.5))

# Adjust layout
plt.tight_layout()

# Save plot
out_path = os.path.join(OUT_DIR, "PVC.png")
plt.savefig(out_path, dpi=300)
plt.close()
