import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.signal import find_peaks

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/17_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

fig_size = (8, 5)
dpi = 600

# Read all sheets from the Excel file
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA structure and the preview
    # Time, Temperature, Weight(%), D.W(%/C)
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight' in str(col):
            weight_col = col
        elif 'D.W' in str(col) or 'DTG' in str(col):
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = df[dtg_col].values
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=fig_size, dpi=dpi)
    
    # Plot Weight (%) on left y-axis
    color1 = '#1f4e9c'
    ax1.set_xlabel('Temperature (°C)', fontsize=10)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=10)
    line1, = ax1.plot(x, y1, color=color1, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=10)
    # Multiply by -1 so peaks point up
    y2_inv = -y2
    line2, = ax2.plot(x, y2_inv, color=color2, label='DTG')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=12)
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # Calculate Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(x - 800))
    residue_val = y1[idx_800]
    temp_residue = x[idx_800]
    
    # Add residue marker and label
    ax1.plot(temp_residue, residue_val, 'o', color=color1, markersize=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(temp_residue, residue_val), 
                 xytext=(temp_residue + 20, residue_val + 5),
                 arrowprops=dict(facecolor=color1, shrink=0.05, width=1, headwidth=5),
                 fontsize=9, color=color1)
                 
    # Find highest DTG peak above 150°C
    # We look at the inverted DTG (peaks pointing up) to find the max value
    mask = x > 150
    x_masked = x[mask]
    y2_inv_masked = y2_inv[mask]
    
    if len(y2_inv_masked) > 0:
        max_idx = np.argmax(y2_inv_masked)
        peak_temp = x_masked[max_idx]
        peak_val_inv = y2_inv_masked[max_idx]
        
        # Marker on the DTG curve (right axis)
        ax2.plot(peak_temp, peak_val_inv, 'o', color=color2, markersize=5)
        # Label near the peak
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_val_inv), 
                     xytext=(peak_temp, peak_val_inv + 0.1),
                     ha='center', va='bottom',
                     fontsize=9, color=color2)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
    output_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(output_path, dpi=dpi)
    plt.close(fig)

