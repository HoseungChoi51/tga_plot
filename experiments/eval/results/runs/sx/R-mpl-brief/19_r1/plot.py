import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/19_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on the preview structure
    # Assuming standard TGA columns: Temperature, Weight(%), D.W(%/C)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and '%' in col_lower:
            weight_col = col
        elif 'd.w' in col_lower or 'dtg' in col_lower or 'derivative' in col_lower:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    line1, = ax1.plot(x, y1, color='#1f4e9c', label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=13, color='gray')
    ax1.set_ylabel('Weight (%)', fontsize=13, color='gray')
    ax1.tick_params(axis='both', labelsize=13, colors='gray')
    ax1.spines['bottom'].set_color('gray')
    ax1.spines['left'].set_color('gray')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Plot DTG on right axis (multiplied by -1 so peaks point up)
    ax2 = ax1.twinx()
    line2, = ax2.plot(x, -y2, color='#c0392b', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', fontsize=13, color='gray')
    ax2.tick_params(axis='both', labelsize=13, colors='gray')
    ax2.spines['bottom'].set_color('gray')
    ax2.spines['right'].set_color('gray')
    ax2.spines['top'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    
    # Title
    ax1.set_title(sheet_name, fontsize=13, color='gray')
    
    # Find residue at 800°C
    mask_800 = ~np.isnan(x) & ~np.isnan(y1)
    if np.any(mask_800):
        idx_800 = np.argmin(np.abs(x[mask_800] - 800))
        temp_800 = x[mask_800][idx_800]
        weight_800 = y1[mask_800][idx_800]
        
        # Marker for residue
        ax1.plot(temp_800, weight_800, 'o', color='#1f4e9c', markersize=5)
        ax1.annotate(f'Residue {weight_800:.1f}%', 
                     xy=(temp_800, weight_800), 
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=13, color='gray')
        
    # Find peak temperature above 150°C from DTG
    # We look for the minimum of original DTG (which becomes maximum after *-1)
    mask_dtg = (x > 150) & ~np.isnan(y2)
    if np.any(mask_dtg):
        # Original DTG is negative during mass loss. Peak is where it's most negative.
        min_dtg_idx = np.nanargmin(y2[mask_dtg])
        peak_temp = x[mask_dtg][min_dtg_idx]
        peak_val = y2[mask_dtg][min_dtg_idx]
        
        # Marker for peak on DTG curve (ax2 uses -y2)
        ax2.plot(peak_temp, -peak_val, 'v', color='#c0392b', markersize=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_val), 
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=13, color='gray')

    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', fontsize=13, frameon=False)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
