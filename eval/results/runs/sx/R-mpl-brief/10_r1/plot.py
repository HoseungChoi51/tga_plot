import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Set Korean font
font_path = None
for f in font_manager.fontManager.ttflist:
    if 'Noto Sans CJK KR' in f.name or 'NotoSansCJKkr' in f.name:
        font_path = f.fname
        break
if font_path:
    prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK KR', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/10_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Identify columns based on typical TGA structure from preview
    # B: Temperature, C: Weight(%), D: D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dtg_col = 'D.W(%/C)'
    
    # Check if columns exist, otherwise try to find them by position/name heuristic
    if temp_col not in df.columns:
        # Fallback: assume col 1 is temp, col 2 is weight, col 3 is dtg if names don't match exactly
        cols = df.columns.tolist()
        if len(cols) >= 4:
            temp_col = cols[1]
            weight_col = cols[2]
            dtg_col = cols[3]
            
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2_raw = df[dtg_col].values
    
    # Filter valid data
    mask = ~np.isnan(x) & ~np.isnan(y1) & ~np.isnan(y2_raw)
    x = x[mask]
    y1 = y1[mask]
    y2_raw = y2_raw[mask]
    
    # DTG multiplied by -1 so peaks point up
    y2 = y2_raw * -1
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    line1 = ax1.plot(x, y1, color='#1f4e9c', label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color='#1f4e9c', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#1f4e9c')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot DTG on right axis
    ax2 = ax1.twinx()
    line2 = ax2.plot(x, y2, color='#c0392b', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color='#c0392b', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5), fontsize=10)
    
    # --- Residue Label at 700 °C with 2 decimal places ---
    target_residue_temp = 700.0
    idx_residue = np.argmin(np.abs(x - target_residue_temp))
    residue_val = y1[idx_residue]
    residue_temp_actual = x[idx_residue]
    
    # Format residue string: "Residue XX.XX%"
    residue_str = f"Residue {residue_val:.2f}%"
    
    # Marker and annotation for residue
    ax1.plot(residue_temp_actual, residue_val, 'o', color='#1f4e9c', markersize=6)
    ax1.annotate(residue_str, 
                 xy=(residue_temp_actual, residue_val), 
                 xytext=(residue_temp_actual + 20, residue_val + 5),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color='#1f4e9c',
                 ha='left', va='bottom')
    
    # --- Peak Label (highest DTG peak above 150 °C) ---
    # Find indices where temperature > 150
    mask_peak_region = x > 150
    if np.any(mask_peak_region):
        y2_filtered = y2[mask_peak_region]
        x_filtered = x[mask_peak_region]
        
        # Find index of max value in filtered array
        idx_max_local = np.argmax(y2_filtered)
        peak_temp = x_filtered[idx_max_local]
        peak_val = y2_filtered[idx_max_local]
        
        # Format peak string: "XXX °C"
        peak_str = f"{peak_temp:.0f} °C"
        
        # Marker and annotation for peak
        ax2.plot(peak_temp, peak_val, 'v', color='#c0392b', markersize=8)
        ax2.annotate(peak_str, 
                     xy=(peak_temp, peak_val), 
                     xytext=(peak_temp, peak_val + 0.1 * np.max(y2)), # Offset slightly above
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                     fontsize=10, color='#c0392b',
                     ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = "".join([c if c.isalnum() else '_' for c in sheet_name])
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

print("Plots saved.")
