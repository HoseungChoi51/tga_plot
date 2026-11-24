import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/05_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on preview info or standard TGA names
    cols = df.columns.tolist()
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        if 'Temperature' in str(c):
            x_col = c
        elif 'Weight' in str(c) and 'D.W' not in str(c) and 'DTG' not in str(c):
            y1_col = c
        elif 'D.W' in str(c) or 'DTG' in str(c):
            y2_col = c
            
    if x_col is None or y1_col is None or y2_col is None:
        continue
        
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (y1) - Black solid line, linewidth 2.5
    color_y1 = 'black'
    ax1.plot(temp, weight, color=color_y1, linewidth=2.5, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    
    # Plot DTG (y2) - Dashed line
    color_y2 = '#c0392b' # Standard red from instructions, though user didn't specify color, just style
    # User asked for "dashed line". Default color is fine unless specified otherwise. 
    # Instructions say right y axis DTG line #c0392b. I will stick to that color but make it dashed.
    ax2.plot(temp, -dtg, color=color_y2, linestyle='--', linewidth=1.5, label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_y2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left', bbox_to_anchor=(0.05, 0.5), frameon=False)
    
    # Residue Label (at ~800 C)
    # Find index closest to 800
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    temp_residue = temp[idx_800]
    
    # Only draw if 800 is within data range roughly
    if min(temp) <= 800 <= max(temp):
        ax1.plot(temp_residue, residue_val, 'o', color=color_y1, markersize=5)
        ax1.annotate(f'Residue {residue_val:.1f}%', xy=(temp_residue, residue_val),
                     xytext=(10, -15), textcoords='offset points',
                     ha='left', va='top', fontsize=10, color=color_y1)
                     
    # Peak Label (highest DTG peak above 150 C)
    # We plotted -dtg, so peaks are positive maxima of -dtg where temp > 150
    mask_temp = temp > 150
    if np.any(mask_temp):
        dtg_plot_vals = -dtg[mask_temp]
        temps_plot_vals = temp[mask_temp]
        
        # Find the maximum value (which corresponds to the most negative original DTG, i.e., fastest mass loss)
        max_idx_local = np.argmax(dtg_plot_vals)
        peak_temp = temps_plot_vals[max_idx_local]
        peak_dtg_val = dtg_plot_vals[max_idx_local]
        
        # Mark on the curve
        ax2.plot(peak_temp, peak_dtg_val, 'o', color=color_y2, markersize=5)
        ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_dtg_val),
                     xytext=(10, 10), textcoords='offset points',
                     ha='left', va='bottom', fontsize=10, color=color_y2)

    # Save plot
    safe_sheet_name = sheet_name.replace(" ", "_").replace("/", "_")
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

print("Plots saved.")
