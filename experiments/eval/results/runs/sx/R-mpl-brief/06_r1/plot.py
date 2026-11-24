import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/06_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on the preview structure
    # Time, Temperature, Weight(%), D.W(%/C)
    x_col = "Temperature"
    y1_col = "Weight(%)"
    y2_col = "D.W(%/C)"
    
    if x_col not in df.columns or y1_col not in df.columns or y2_col not in df.columns:
        continue
        
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left y-axis (y1)
    color_y1 = '#1f4e9c'
    line1, = ax1.plot(temp, weight, color=color_y1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Create twin axis for DTG
    ax2 = ax1.twinx()
    color_y2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    line2, = ax2.plot(temp, -dtg, color=color_y2, label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_y2)
    
    # Title is the sheet name
    ax1.set_title(sheet_name, fontsize=14)
    
    # User request: Remove legend, Turn on grid
    # ax1.legend(loc='center left') # Removed per request
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Calculate Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    residue_temp = temp[idx_800]
    
    # Add marker and text for residue
    ax1.scatter(residue_temp, residue_val, color=color_y1, s=50, zorder=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 20, residue_val + 5),
                 arrowprops=dict(arrowstyle='->', color=color_y1),
                 fontsize=10, color=color_y1)
    
    # Calculate Peak temperature of highest DTG peak above 150°C
    # Filter data where temp > 150
    mask_peak = temp > 150
    if np.any(mask_peak):
        temp_filtered = temp[mask_peak]
        dtg_filtered = dtg[mask_peak]
        
        # Find index of minimum DTG (most negative) which corresponds to max mass loss rate
        # Since we plot -dtg, the peak in the plot is the max of -dtg, which is min of dtg
        idx_min_dtg = np.argmin(dtg_filtered)
        peak_temp = temp_filtered[idx_min_dtg]
        peak_dtg_val = dtg_filtered[idx_min_dtg]
        
        # Add marker and text for peak on ax2
        ax2.scatter(peak_temp, -peak_dtg_val, color=color_y2, s=50, zorder=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, -peak_dtg_val), 
                     xytext=(peak_temp + 20, -peak_dtg_val + 0.1),
                     arrowprops=dict(arrowstyle='->', color=color_y2),
                     fontsize=10, color=color_y2)
    
    # Adjust layout to prevent label cutoff
    fig.tight_layout()
    
    # Save figure
    safe_sheet_name = sheet_name.replace(" ", "_").replace("/", "_")
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
