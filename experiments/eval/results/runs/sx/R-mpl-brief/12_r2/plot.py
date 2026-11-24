import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

# Configure fonts for Korean text
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/12_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets from the Excel file
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on standard TGA structure or headers provided in preview
    # Assuming standard order: Time, Temperature, Weight(%), D.W(%/C)
    # We look for columns containing 'Temp', 'Weight', 'D.W' or similar if names vary, 
    # but here they seem consistent.
    
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        c_lower = str(col).lower()
        if 'temp' in c_lower:
            temp_col = col
        elif 'weight' in c_lower and 'd.w' not in c_lower and 'derivative' not in c_lower:
            weight_col = col
        elif 'd.w' in c_lower or 'derivative' in c_lower or 'dtg' in c_lower:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    line1 = ax1.plot(x, y1, color='#1f4e9c', label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)')
    ax1.set_ylabel('Weight (%)', color='#1f4e9c')
    ax1.tick_params(axis='y', labelcolor='#1f4e9c')
    
    # Plot DTG on right axis, multiplied by -1 to make peaks point up
    ax2 = ax1.twinx()
    line2 = ax2.plot(x, y2 * -1, color='#c0392b', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color='#c0392b')
    ax2.tick_params(axis='y', labelcolor='#c0392b')
    
    # Title
    ax1.set_title(sheet_name)
    
    # Legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # Add vertical reference line at 450 °C
    ref_temp = 450
    ax1.axvline(x=ref_temp, color='gray', linestyle='--', linewidth=1)
    
    # Add text annotation '산화 시작' near the top of the line
    # Find y position: use the max of y1 range to place it nicely at the top
    y_min, y_max = ax1.get_ylim()
    text_y_pos = y_max - (y_max - y_min) * 0.1 # 10% down from top
    
    ax1.text(ref_temp + 5, text_y_pos, '산화 시작', rotation=90, va='top', ha='left', fontsize=10, color='black')
    
    # Calculate Residue at nearest 800°C (if available in data range)
    # The prompt says "residue: the weight at the measured point nearest 800 °C"
    target_residue_temp = 800
    idx_residue = np.argmin(np.abs(x - target_residue_temp))
    residue_val = y1[idx_residue]
    residue_temp_actual = x[idx_residue]
    
    # Only plot marker and label if we have a valid value
    if not np.isnan(residue_val):
        ax1.plot(residue_temp_actual, residue_val, 'o', color='#1f4e9c', markersize=5)
        ax1.annotate(f'Residue {residue_val:.1f}%', 
                     xy=(residue_temp_actual, residue_val), 
                     xytext=(10, -15), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5'),
                     fontsize=9, color='#1f4e9c')
        
    # Calculate Peak temperature: highest DTG peak above 150 °C
    # DTG is negative during mass loss, so we look for minimum in original y2 (or maximum in -y2)
    mask_peak = x > 150
    if np.any(mask_peak):
        y2_masked = y2[mask_peak]
        x_masked = x[mask_peak]
        
        # Find index of minimum in original y2 (which corresponds to max magnitude of mass loss)
        # Note: y2 is already negative for loss. So min(y2) is the most negative, i.e., largest loss rate.
        idx_peak_local = np.argmin(y2_masked)
        peak_temp = x_masked[idx_peak_local]
        peak_dtg_val = y2_masked[idx_peak_local]
        
        # Plot marker on DTG curve (on ax2)
        # We need to map back to global indices or just use the masked values for plotting coordinates
        # Since ax2 plots x vs -y2, the coordinate for the peak on the plot is (peak_temp, -peak_dtg_val)
        
        ax2.plot(peak_temp, -peak_dtg_val, 'o', color='#c0392b', markersize=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_dtg_val), 
                     xytext=(-15, 10), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=-0.5'),
                     fontsize=9, color='#c0392b')

    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).strip().replace(' ', '_')
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
