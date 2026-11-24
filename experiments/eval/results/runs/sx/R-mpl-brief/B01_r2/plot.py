import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Set Korean font
font_path = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
if not font_manager.findfont('Noto Sans CJK KR'):
    try:
        font_manager.fontManager.addfont(font_path)
    except:
        pass
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Load data
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/caox.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B01_r2/out"

df = pd.read_csv(DATA_FILE)

# Extract columns based on preview
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

temperature = df[temp_col].values
weight = df[weight_col].values
dtg = df[dtg_col].values

# Define regions and colors
regions = [
    {"start": 120, "end": 250, "label": "H2O", "color": "#a8dadc"},
    {"start": 430, "end": 580, "label": "CO", "color": "#f1faee"},
    {"start": 640, "end": 830, "label": "CO2", "color": "#e63946"}
]

# Create plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight (%) on left y-axis
line1 = ax1.plot(temperature, weight, color='#1f4e9c', linewidth=1.5, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#1f4e9c')

# Create second y-axis for DTG
ax2 = ax1.twinx()
# Multiply DTG by -1 so peaks point up
dtg_neg = dtg * -1
line2 = ax2.plot(temperature, dtg_neg, color='#c0392b', linewidth=1.5, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#c0392b')

# Add shaded regions and labels
for region in regions:
    start = region["start"]
    end = region["end"]
    label = region["label"]
    color = region["color"]
    
    # Shade the region on the primary axis (ax1)
    ax1.axvspan(start, end, alpha=0.3, color=color, zorder=0)
    
    # Find a suitable y-position for the text label within the region
    # Use the average of the weight values in that range to place the label roughly in the middle vertically relative to the curve, or just use a fixed offset from the top/bottom.
    # Let's find the max weight in the region to place the label above it but below the top of the plot area if possible, or simply center it vertically in the plot area for clarity since the curves vary.
    mask = (temperature >= start) & (temperature <= end)
    if np.any(mask):
        avg_weight = np.mean(weight[mask])
        # Place label slightly above the average weight in the region
        y_pos = avg_weight + 5 
    else:
        y_pos = 50 # fallback
        
    # Ensure label is visible
    if y_pos > 100:
        y_pos = 95
        
    ax1.text((start + end) / 2, y_pos, label, ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

# Calculate Residue at ~800°C
idx_800 = np.argmin(np.abs(temperature - 800))
residue_val = weight[idx_800]
residue_temp = temperature[idx_800]
ax1.plot(residue_temp, residue_val, 'o', color='#1f4e9c', markersize=8, zorder=5)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val), 
             xytext=(residue_temp - 50, residue_val + 10),
             arrowprops=dict(facecolor='black', shrink=0.05),
             fontsize=10, color='black')

# Calculate Peak Temperature (>150°C)
mask_peak = temperature > 150
if np.any(mask_peak):
    # Find index of max dtg_neg (which corresponds to min original dtg)
    dtg_neg_masked = dtg_neg.copy()
    dtg_neg_masked[~mask_peak] = -np.inf
    peak_idx = np.argmax(dtg_neg_masked)
    peak_temp = temperature[peak_idx]
    peak_dtg_val = dtg_neg[peak_idx]
    
    ax2.plot(peak_temp, peak_dtg_val, 'o', color='#c0392b', markersize=8, zorder=5)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_dtg_val), 
                 xytext=(peak_temp + 20, peak_dtg_val + 0.05),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 fontsize=10, color='black')

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.02, 0.5))

# Title
title_text = "caox"
plt.title(title_text, fontsize=14, pad=10)

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

# Save figure
import os
os.makedirs(OUT_DIR, exist_ok=True)
output_path = os.path.join(OUT_DIR, f"{title_text}.png")
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
