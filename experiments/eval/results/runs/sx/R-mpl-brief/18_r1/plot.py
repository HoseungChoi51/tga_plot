import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/18_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Identify columns based on standard TGA structure or guessing from preview
    cols = df.columns.tolist()
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        cl = str(c).lower()
        if 'temperature' in cl or 'temp' in cl:
            x_col = c
        elif 'weight' in cl and '%' in cl and 'd.w' not in cl and 'dtg' not in cl:
            y1_col = c
        elif 'd.w' in cl or 'dtg' in cl or ('weight' in cl and '/' in cl):
            y2_col = c
            
    if x_col is None: x_col = cols[1]
    if y1_col is None: y1_col = cols[2]
    if y2_col is None: y2_col = cols[3]

    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    # Filter valid data
    mask = ~np.isnan(temp) & ~np.isnan(weight) & ~np.isnan(dtg)
    temp = temp[mask]
    weight = weight[mask]
    dtg = dtg[mask]
    
    # Sort by temperature just in case
    idx = np.argsort(temp)
    temp = temp[idx]
    weight = weight[idx]
    dtg = dtg[idx]

    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    # Plot Weight (y1)
    color1 = '#1f4e9c'
    ax1.plot(temp, weight, color=color1, label='Weight (%)')
    ax1.set_xlabel('Temperature (°C)', fontsize=12)
    ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # X-axis tick interval 100
    ax1.set_xticks(np.arange(0, max(temp)+100, 100))
    
    # Create twin axis for DTG (y2)
    ax2 = ax1.twinx()
    color2 = '#c0392b'
    # Multiply DTG by -1 so peaks point up
    dtg_plot = dtg * -1
    ax2.plot(temp, dtg_plot, color=color2, label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Y2 axis range -0.05 to 1.2
    ax2.set_ylim(-0.05, 1.2)
    
    # Find Residue at nearest 800°C
    target_temp = 800
    idx_res = np.argmin(np.abs(temp - target_temp))
    residue_val = weight[idx_res]
    residue_temp = temp[idx_res]
    
    # Mark residue
    ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=8)
    ax1.annotate(f'Residue {residue_val:.1f}%', 
                 xy=(residue_temp, residue_val), 
                 xytext=(residue_temp + 20, residue_val + 5),
                 arrowprops=dict(facecolor=color1, shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color=color1)
                 
    # Find Peak above 150°C
    mask_peak = temp > 150
    if np.any(mask_peak):
        dtg_valid = dtg_plot[mask_peak]
        temp_valid = temp[mask_peak]
        idx_max = np.argmax(dtg_valid)
        peak_temp = temp_valid[idx_max]
        peak_val = dtg_valid[idx_max]
        
        # Mark peak
        ax2.plot(peak_temp, peak_val, 'v', color=color2, markersize=8)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_val), 
                     xytext=(peak_temp - 30, peak_val + 0.1),
                     arrowprops=dict(facecolor=color2, shrink=0.05, width=1, headwidth=5),
                     fontsize=10, color=color2)

    # Title
    ax1.set_title(sheet_name, fontsize=14, fontweight='bold')
    
    # Legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center left', bbox_to_anchor=(0.02, 0.5))
    
    plt.tight_layout()
    
    out_path = os.path.join(OUT_DIR, f"{sheet_name.replace(' ', '_').replace('/', '_')}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

print("Plots saved.")
