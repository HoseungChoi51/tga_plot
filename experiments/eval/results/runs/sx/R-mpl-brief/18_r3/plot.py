import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/18_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA structure from preview
    # Assuming: Time (A), Temperature (B), Weight% (C), DTG (D)
    cols = df.columns.tolist()
    
    # Heuristic to find columns if names vary slightly, but using known names from preview
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temp' in c_lower or '온도' in c_lower:
            x_col = c
        elif 'weight' in c_lower and '%' in c_lower and 'd.w' not in c_lower and 'derivative' not in c_lower:
            y1_col = c
        elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower or ('weight' in c_lower and '/' in c_lower):
            y2_col = c
            
    # Fallback to positional if heuristic fails
    if x_col is None and len(cols) >= 2: x_col = cols[1]
    if y1_col is None and len(cols) >= 3: y1_col = cols[2]
    if y2_col is None and len(cols) >= 4: y2_col = cols[3]

    if x_col is None or y1_col is None or y2_col is None:
        continue
        
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color_y1 = '#1f4e9c'
    ax1.plot(temp, weight, color=color_y1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Set X-axis tick interval to 100
    ax1.set_xticks(np.arange(0, max(temp)+100, 100))
    
    # Create right axis for DTG
    ax2 = ax1.twinx()
    color_y2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    ax2.plot(temp, -dtg, color=color_y2, label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_y2)
    
    # Set Y2 axis range as requested: -0.05 ~ 1.2
    ax2.set_ylim(-0.05, 1.2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left')
    
    # Calculate Residue at nearest 800°C
    mask_800 = (temp >= 790) & (temp <= 810)
    if not np.any(mask_800):
         # If no data near 800, take the last point if max temp < 800, or closest overall
         idx_res = np.argmin(np.abs(temp - 800))
    else:
         # Take average of points in window or closest single point? Usually closest single point is safer for labeling
         idx_res = np.argmin(np.abs(temp[mask_800] - 800))
         # Get actual index in original array
         indices = np.where(mask_800)[0]
         idx_res = indices[idx_res]
         
    residue_val = weight[idx_res]
    residue_temp = temp[idx_res]
    
    # Mark residue
    ax1.plot(residue_temp, residue_val, 'o', color=color_y1, markersize=8)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp - 50, residue_val + 5),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 fontsize=10, color=color_y1)
                 
    # Calculate Peak temperature (highest DTG peak above 150°C)
    # We look for the minimum of original DTG (which becomes maximum after *-1) above 150C
    mask_peak = temp > 150
    if np.any(mask_peak):
        dtg_subset = dtg[mask_peak]
        temp_subset = temp[mask_peak]
        
        # Find index of minimum DTG value (most negative -> highest positive peak after inversion)
        min_dtg_idx_local = np.argmin(dtg_subset)
        peak_temp = temp_subset[min_dtg_idx_local]
        peak_dtg_val = dtg_subset[min_dtg_idx_local]
        
        # Mark peak on DTG curve (inverted)
        ax2.plot(peak_temp, -peak_dtg_val, 'o', color=color_y2, markersize=8)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_dtg_val), 
                     xytext=(peak_temp + 20, -peak_dtg_val + 0.1),
                     arrowprops=dict(facecolor='black', shrink=0.05),
                     fontsize=10, color=color_y2)
    
    # Grid
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Save
    safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

