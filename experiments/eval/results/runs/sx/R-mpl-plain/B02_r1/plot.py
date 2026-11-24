import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B02_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read data
df = pd.read_csv(DATA_FILE)

# Extract columns
temp = df['Temperature (°C)'].values
weight = df['Weight (%)'].values
heat_flow = df['Heat Flow (W/g)'].values

# Find peaks in Heat Flow
# Endothermic peaks: positive heat flow values
# Exothermic peaks: negative heat flow values

# For endothermic peaks (positive), we look for local maxima
endothermic_peaks, endo_properties = find_peaks(heat_flow, height=0.5, distance=10)
# For exothermic peaks (negative), we look for local minima by finding peaks of -heat_flow
exothermic_peaks, exo_properties = find_peaks(-heat_flow, height=0.5, distance=10)

# Sort and select top 2 endothermic and top 1 exothermic if needed
if len(endothermic_peaks) > 2:
    # Select the two highest endothermic peaks
    heights = heat_flow[endothermic_peaks]
    sorted_idx = np.argsort(heights)[::-1][:2]
    endothermic_peaks = endothermic_peaks[sorted_idx]

if len(exothermic_peaks) > 1:
    # Select the most prominent exothermic peak
    depths = -heat_flow[exothermic_peaks]
    sorted_idx = np.argsort(depths)[::-1][:1]
    exothermic_peaks = exothermic_peaks[sorted_idx]

# Create figure with twin axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot TGA on left axis
ax1.plot(temp, weight, color='blue', label='TGA (Weight %)', linewidth=2)
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# Create twin axis for Heat Flow
ax2 = ax1.twinx()
ax2.plot(temp, heat_flow, color='red', label='Heat Flow (W/g)', linewidth=2)
ax2.set_ylabel('Heat Flow (W/g)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# Mark endothermic peaks (positive heat flow)
for i, peak_idx in enumerate(endothermic_peaks):
    temp_peak = temp[peak_idx]
    hf_peak = heat_flow[peak_idx]
    ax2.annotate(f'Endo {i+1}\n{temp_peak:.1f}°C', 
                 xy=(temp_peak, hf_peak), 
                 xytext=(temp_peak + 30, hf_peak + 0.3),
                 arrowprops=dict(arrowstyle='->', color='green'),
                 fontsize=9, color='green', ha='left')
    ax2.plot(temp_peak, hf_peak, 'go', markersize=8)

# Mark exothermic peaks (negative heat flow)
for i, peak_idx in enumerate(exothermic_peaks):
    temp_peak = temp[peak_idx]
    hf_peak = heat_flow[peak_idx]
    ax2.annotate(f'Exo {i+1}\n{temp_peak:.1f}°C', 
                 xy=(temp_peak, hf_peak), 
                 xytext=(temp_peak + 30, hf_peak - 0.5),
                 arrowprops=dict(arrowstyle='->', color='orange'),
                 fontsize=9, color='orange', ha='left')
    ax2.plot(temp_peak, hf_peak, 'o', color='orange', markersize=8)

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

ax1.set_title('TGA와 Heat Flow 분석', fontsize=14)
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "tga_heatflow.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
