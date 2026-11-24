import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Data file and output directory
DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/03_r1/out"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet
sheet_name = "1006R1-V acid"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# Identify columns based on standard TGA structure from preview
# Time: A, Temperature: B, Weight(%): C, D.W(%/C): D
x_col = 'Temperature'
y1_col = 'Weight(%)'
y2_col = 'D.W(%/C)'

# Extract data
temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Filter for x-axis range 100~800 for plotting purposes (though we need full data for peak finding logic if peaks are outside? 
# The request says "x축 범위 100~800", which usually means set xlim. 
# However, "피크 표시 2개" implies finding the top 2 peaks. 
# Standard TGA plots often show the whole range or relevant decomposition range. 
# If I strictly limit the data to 100-800 before peak finding, I might miss a peak <100 or >800 if it exists. 
# But typically decomposition happens in this range. Let's filter data for plotting and peak finding within this range to be safe and consistent with the view.
mask = (temp >= 100) & (temp <= 800)
temp_plot = temp[mask]
weight_plot = weight[mask]
dtg_plot = dtg[mask]

# Prepare DTG for plotting (multiply by -1 so peaks point up)
dtg_plot_neg = -1 * dtg_plot

# Find peaks in DTG (above 150 C is standard rule, but user didn't specify min temp for peak search, just x-range. 
# The prompt says "highest DTG peak above 150 °C". We will look for peaks in the filtered data.)
# We use find_peaks on the negative DTG (which makes losses positive peaks).
# distance parameter helps avoid noise, height threshold too.
peaks, properties = find_peaks(dtg_plot_neg, distance=50, height=0.05) # Adjusted params for robustness

if len(peaks) == 0:
    # Fallback if no peaks found with strict criteria
    peaks, properties = find_peaks(dtg_plot_neg, distance=20)

# Sort peaks by height (magnitude of mass loss rate) descending
peak_heights = properties['peak_heights']
sorted_indices = np.argsort(peak_heights)[::-1]
top_2_peak_indices = sorted_indices[:2]

# Get temperatures and values for the top 2 peaks
peak_temps = []
peak_vals = []
for idx in top_2_peak_indices:
    t = temp_plot[idx]
    v = dtg_plot_neg[idx]
    peak_temps.append(t)
    peak_vals.append(v)

# Plotting
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
fig, ax1 = plt.subplots(figsize=(8, 6))

color_y1 = '#1f4e9c'
color_y2 = '#c0392b'

ax1.plot(temp_plot, weight_plot, color=color_y1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_y1)
ax1.set_xlim(100, 800)

ax2 = ax1.twinx()
ax2.plot(temp_plot, dtg_plot_neg, color=color_y2, label='DTG (-%/°C)')
ax2.set_ylabel('DTG (-%/°C)', color=color_y2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color_y2)

# Title
ax1.set_title(sheet_name, fontsize=14)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

# Add Residue Label
# Find weight at nearest 800 C within the plot range
idx_residue = np.argmin(np.abs(temp_plot - 800))
res_temp = temp_plot[idx_residue]
res_weight = weight_plot[idx_residue]

ax1.plot(res_temp, res_weight, 'o', color=color_y1, markersize=5)
ax1.annotate(f'Residue {res_weight:.1f}%', xy=(res_temp, res_weight), xytext=(10, 10),
             textcoords='offset points', fontsize=10, color=color_y1,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color_y1, alpha=0.8))

# Add Peak Labels
for i, (pt, pv) in enumerate(zip(peak_temps, peak_vals)):
    # Find corresponding weight value at peak temperature for marker position on DTG curve
    # Note: PV is already the negated DTG value used for plotting
    ax2.plot(pt, pv, 'v', color=color_y2, markersize=5)
    # Offset slightly to avoid overlap
    offset_y = 10 if i == 0 else 25
    ax2.annotate(f'{pt:.0f} °C', xy=(pt, pv), xytext=(0, offset_y),
                 textcoords='offset points', ha='center', fontsize=10, color=color_y2,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color_y2, alpha=0.8))

plt.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, f"{sheet_name.replace(' ', '_')}.png")
plt.savefig(out_path, dpi=300)
plt.close()
