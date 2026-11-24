import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/09_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(xl_file, sheet_name=sheet_name)
    
    # Identify columns based on standard TGA structure from preview
    # Assuming: Time (A), Temperature (B), Weight(%) (C), D.W(%/C) (D)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'temp' in col_str or col == 'Temperature':
            temp_col = col
        elif 'weight' in col_str and '%' in col_str and 'd.w' not in col_str:
            weight_col = col
        elif 'd.w' in col_str or 'dtg' in col_str:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    temps = df[temp_col].values
    weights = df[weight_col].values
    dtgs = df[dtg_col].values
    
    # Create figure and axes
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left y-axis
    color1 = '#1f4e9c'
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    line1, = ax1.plot(temps, weights, color=color1, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color1, direction='out', labelsize=9)
    ax1.tick_params(axis='x', direction='out', labelsize=9)
    
    # Create second y-axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
    # Multiply by -1 to make peaks point up
    line2, = ax2.plot(temps, -dtgs, color=color2, label='DTG')
    ax2.tick_params(axis='y', labelcolor=color2, direction='out', labelsize=9)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5), frameon=False)
    
    # Find Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temps - 800))
    residue_val = weights[idx_800]
    residue_temp = temps[idx_800]
    
    # Add marker and label for residue
    ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=6)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 20, residue_val - 10),
                 arrowprops=dict(facecolor=color1, shrink=0.05),
                 fontsize=9, color=color1)
                 
    # Find Peak of DTG above 150°C
    mask_high_temp = temps > 150
    if np.any(mask_high_temp):
        dtg_subset = dtgs[mask_high_temp]
        temp_subset = temps[mask_high_temp]
        
        # Find index of minimum DTG (most negative) which corresponds to max mass loss rate
        min_dtg_idx_local = np.argmin(dtg_subset)
        peak_temp = temp_subset[min_dtg_idx_local]
        peak_dtg_val = dtg_subset[min_dtg_idx_local]
        
        # Plot marker on the inverted DTG curve (ax2)
        # Since we plotted -dtgs, the peak value on the plot is -peak_dtg_val
        ax2.plot(peak_temp, -peak_dtg_val, 'o', color=color2, markersize=6)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_dtg_val), 
                     xytext=(peak_temp - 30, -peak_dtg_val * 1.1),
                     arrowprops=dict(facecolor=color2, shrink=0.05),
                     fontsize=9, color=color2)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).strip()
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
