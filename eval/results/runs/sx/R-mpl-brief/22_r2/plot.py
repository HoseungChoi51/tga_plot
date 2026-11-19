import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/22_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on the preview structure
    # A: Time, B: Temperature, C: Weight(%), D: D.W(%/C)
    x_col = None
    y1_col = None
    y2_col = None
    
    cols = df.columns.tolist()
    for c in cols:
        cl = str(c).lower()
        if 'temp' in cl or 'temperature' in cl:
            x_col = c
        elif 'weight' in cl and '%' in cl and 'd.w' not in cl and 'derivative' not in cl:
            y1_col = c
        elif 'd.w' in cl or 'dtg' in cl or 'derivative' in cl:
            y2_col = c
            
    # Fallback to indices if names aren't clear (based on preview: 0=Time, 1=Temp, 2=Weight, 3=DW)
    if x_col is None: x_col = cols[1]
    if y1_col is None: y1_col = cols[2]
    if y2_col is None: y2_col = cols[3]
    
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Prepare data for plotting
    # DTG multiplied by -1 so peaks point up
    dtg_plot = dtg * -1
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (%) on left axis
    color_y1 = '#1f4e9c'
    line1, = ax1.plot(temp, weight, color=color_y1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color_y1)
    
    # Create secondary axis for DTG
    ax2 = ax1.twinx()
    # User request: y2 line color green, y2 axis label text color green
    color_y2 = 'green'
    line2, = ax2.plot(temp, dtg_plot, color=color_y2, linestyle='--', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color=color_y2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color_y2)
    
    # Title
    ax1.set_title(sheet_name, fontsize=14)
    
    # Legend
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')
    
    # Find Residue at nearest 800°C
    idx_800 = np.argmin(np.abs(temp - 800))
    residue_val = weight[idx_800]
    residue_temp = temp[idx_800]
    
    # Add residue marker and label
    ax1.scatter(residue_temp, residue_val, color=color_y1, zorder=5)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 20, residue_val + 5),
                 arrowprops=dict(arrowstyle="->", color=color_y1),
                 color=color_y1, fontsize=10)
                 
    # Find Peak temperature of highest DTG peak above 150°C
    mask = temp > 150
    if np.any(mask):
        dtg_masked = dtg[mask]
        temp_masked = temp[mask]
        
        # Since we plotted dtg * -1, the "highest peak" visually corresponds to the most negative original DTG value.
        # However, usually "peak" refers to the maximum magnitude of mass loss rate.
        # In the plot, dtg_plot = -dtg. So max(dtg_plot) corresponds to min(dtg).
        idx_peak_local = np.argmax(dtg_masked) # This finds the most negative original DTG, which becomes the highest positive value in dtg_plot
        
        peak_temp = temp_masked[idx_peak_local]
        peak_dtg_val = dtg_plot[idx_peak_local] # Value on the right axis scale
        
        # Add peak marker and label
        # Marker on the curve (which is on ax2)
        ax2.scatter(peak_temp, peak_dtg_val, color=color_y2, zorder=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_dtg_val), 
                     xytext=(peak_temp - 50, peak_dtg_val + 0.1), # Adjust position slightly
                     arrowprops=dict(arrowstyle="->", color=color_y2),
                     color=color_y2, fontsize=10)
    
    # Grid
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # Save figure
    safe_sheet_name = "".join([i if i.isalnum() or i in ['-', '_'] else '_' for i in sheet_name])
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
