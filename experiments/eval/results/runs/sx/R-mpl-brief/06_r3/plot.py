import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/06_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=1)
    
    # Identify columns based on standard TGA structure or guess from preview
    cols = df.columns.tolist()
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        c_lower = str(c).lower()
        if 'temperature' in c_lower or 'temp' in c_lower:
            x_col = c
        elif 'weight' in c_lower and '%' in str(c):
            y1_col = c
        elif 'd.w' in c_lower or 'dtg' in c_lower or 'derivative' in c_lower:
            y2_col = c
            
    if x_col is None: x_col = cols[1]
    if y1_col is None: y1_col = cols[2]
    if y2_col is None: y2_col = cols[3]
    
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (y1)
    color1 = '#1f4e9c'
    ax1.plot(temp, weight, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Plot DTG (y2) - multiply by -1 to make peaks point up
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    ax2.plot(temp, -dtg, color=color2, linestyle='--', label='DTG (-% / °C)')
    ax2.set_ylabel('DTG (-% / °C)', color=color2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Calculate Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temp - 800.0))
    residue_val = weight[idx_800]
    residue_temp = temp[idx_800]
    
    # Mark residue
    ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=8)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(10, -15), textcoords='offset points',
                 fontsize=10, color=color1,
                 arrowprops=dict(arrowstyle='->', color=color1))
                 
    # Find highest DTG peak above 150°C
    mask = temp > 150
    if np.any(mask):
        dtg_positive = -dtg[mask] # We plotted -dtg, so we look for max of this
        temps_masked = temp[mask]
        
        # Smooth slightly or just find local maxima? Simple argmax on positive values usually works for main peak
        # To be robust, let's find the global max of the inverted DTG curve in that range
        max_idx_rel = np.argmax(dtg_positive)
        peak_temp = temps_masked[max_idx_rel]
        peak_dtg_val = dtg_positive[max_idx_rel]
        
        # Mark peak
        ax2.plot(peak_temp, peak_dtg_val, 'v', color=color2, markersize=8)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_dtg_val), 
                     xytext=(-10, 10), textcoords='offset points',
                     fontsize=10, color=color2,
                     arrowprops=dict(arrowstyle='->', color=color2))

    # User Request: Remove legend, Turn on grid
    # No legend call needed effectively removes it if not called, but explicitly ensuring no legend box
    # ax1.legend() is skipped.
    
    # Grid
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Save
    safe_sheet_name = sheet_name.replace(" ", "_").replace("/", "_")
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

print("Plots saved.")
