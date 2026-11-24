import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/10_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA structure from preview
    # Columns: Time, Temperature, Weight(%), D.W(%/C)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'temperature' in col_str or 'temp' in col_str:
            temp_col = col
        elif 'weight' in col_str and '%' in col_str:
            weight_col = col
        elif 'd.w' in col_str or 'dtg' in col_str or 'derivative' in col_str:
            dtg_col = col
            
    # Fallback to positional if names don't match well
    if temp_col is None and len(df.columns) >= 2:
        temp_col = df.columns[1]
    if weight_col is None and len(df.columns) >= 3:
        weight_col = df.columns[2]
    if dtg_col is None and len(df.columns) >= 4:
        dtg_col = df.columns[3]
        
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color_y1 = '#1f4e9c'
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    line1, = ax1.plot(x, y1, color=color_y1, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Plot DTG on right axis
    ax2 = ax1.twinx()
    color_y2 = '#c0392b'
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    
    if dtg_col is not None:
        y2_raw = df[dtg_col].values
        # Invert sign so peaks point up
        y2 = -y2_raw 
        line2, = ax2.plot(x, y2, color=color_y2, linestyle='--', label='DTG')
        ax2.tick_params(axis='y', labelcolor=color_y2)
    else:
        line2 = None
        
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines = [line1]
    labels = ['Weight']
    if line2 is not None:
        lines.append(line2)
        labels.append('DTG')
    ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.05, 0.5))
    
    # --- Custom Residue Calculation at 700°C with 2 decimal places ---
    target_temp = 700.0
    
    # Find the index closest to 700°C
    idx_closest = np.argmin(np.abs(x - target_temp))
    residue_val = y1[idx_closest]
    actual_temp_at_residue = x[idx_closest]
    
    # Format residue string with 2 decimal places
    residue_label = f"Residue {residue_val:.2f}%"
    
    # Mark the residue point
    ax1.plot(actual_temp_at_residue, residue_val, 'o', color=color_y1, markersize=6)
    # Add text annotation near the point
    # Offset slightly to avoid overlapping the curve
    ax1.annotate(residue_label, 
                 xy=(actual_temp_at_residue, residue_val), 
                 xytext=(actual_temp_at_residue + 20, residue_val + 5),
                 fontsize=10, color=color_y1,
                 arrowprops=dict(facecolor=color_y1, shrink=0.05, width=1, headwidth=4))

    # --- Peak Calculation (Standard behavior: highest DTG peak above 150°C) ---
    if dtg_col is not None:
        # Filter data above 150°C
        mask = x > 150
        if np.any(mask):
            x_filtered = x[mask]
            y2_filtered = y2[mask] # Already inverted
            
            # Find max of inverted DTG (which corresponds to most negative original DTG)
            idx_peak = np.argmax(y2_filtered)
            peak_temp = x_filtered[idx_peak]
            peak_val = y2_filtered[idx_peak]
            
            peak_label = f"{peak_temp:.0f} °C"
            
            # Mark the peak
            ax2.plot(peak_temp, peak_val, 'v', color=color_y2, markersize=6)
            ax2.annotate(peak_label, 
                         xy=(peak_temp, peak_val), 
                         xytext=(peak_temp + 20, peak_val + 0.1 * abs(max(y2))), # Dynamic offset
                         fontsize=10, color=color_y2,
                         arrowprops=dict(facecolor=color_y2, shrink=0.05, width=1, headwidth=4))

    # Grid
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Save
    safe_sheet_name = "".join([c if c.isalnum() or c in (' ', '-', '_') else '_' for c in sheet_name]).strip()
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

print("Plots saved.")
