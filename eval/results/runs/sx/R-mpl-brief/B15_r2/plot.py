import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B15_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

colors_y1 = ['#1f4e9c', '#2ecc71', '#8e44ad']
colors_y2 = ['#c0392b', '#f39c12', '#34495e']

for idx, sheet in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    
    # Identify columns by name patterns
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and 'deriv' not in col_lower and 'dtg' not in col_lower:
            weight_col = col
        elif 'deriv' in col_lower or 'dtg' in col_lower:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Plot Weight (%) on left axis
    line1, = ax1.plot(x, y1, color=colors_y1[idx % len(colors_y1)], label=f'{sheet} Weight', linewidth=1.5)
    
    # Plot DTG on right axis (inverted so peaks point up)
    line2, = ax2.plot(x, -y2, color=colors_y2[idx % len(colors_y2)], label=f'{sheet} DTG', linewidth=1.5)
    
    # Calculate Residue at ~800°C
    mask_800 = np.abs(x - 800) < 5
    if np.any(mask_800):
        residue_val = y1[mask_800][np.argmin(np.abs(x[mask_800] - 800))]
        residue_temp = x[mask_800][np.argmin(np.abs(x[mask_800] - 800))]
        ax1.plot(residue_temp, residue_val, 'o', color=colors_y1[idx % len(colors_y1)], markersize=5)
        ax1.annotate(f'Residue {residue_val:.1f}%', 
                     xy=(residue_temp, residue_val), 
                     xytext=(10, -15), textcoords='offset points',
                     fontsize=8, color=colors_y1[idx % len(colors_y1)])
                     
    # Calculate Peak temperature (>150°C) from DTG
    # We look for the most negative value in original DTG (which becomes highest positive in -DTG)
    # But strictly speaking, we want the peak of mass loss rate.
    # Original DTG is negative during loss. Max loss rate = min(DTG).
    # In our plot, we plotted -DTG. So max(-DTG) corresponds to min(DTG).
    valid_mask = x > 150
    if np.any(valid_mask):
        dtg_valid = y2[valid_mask]
        temp_valid = x[valid_mask]
        
        # Find index of minimum DTG (maximum mass loss rate)
        idx_min_dtg = np.argmin(dtg_valid)
        peak_temp = temp_valid[idx_min_dtg]
        peak_dtg_val = dtg_valid[idx_min_dtg]
        
        # Mark on the inverted DTG curve (ax2)
        ax2.plot(peak_temp, -peak_dtg_val, 'v', color=colors_y2[idx % len(colors_y2)], markersize=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_dtg_val), 
                     xytext=(0, 10), textcoords='offset points',
                     ha='center', fontsize=8, color=colors_y2[idx % len(colors_y2)])

# Axis Labels
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12, color='#1f4e9c')
ax2.set_ylabel('DTG (%/°C) [Inverted]', fontsize=12, color='#c0392b')

# Title
plt.title('TGA Analysis: PE, PVC, PET', fontsize=14)

# Legend outside right
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
all_lines = lines1 + lines2
all_labels = labels1 + labels2

legend = ax1.legend(all_lines, all_labels, loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0., fontsize=10)

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'tga_combined.png'), dpi=300, bbox_inches='tight')
plt.close()
