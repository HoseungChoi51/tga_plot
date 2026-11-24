import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/08_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

for sheet_name in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on the preview info / standard TGA structure
    # Time, Temperature, Weight(%), D.W(%/C)
    cols = df.columns.tolist()
    
    x_col = None
    y1_col = None
    y2_col = None
    
    for c in cols:
        if 'temperature' in str(c).lower():
            x_col = c
        elif 'weight' in str(c).lower() and 'd.w' not in str(c).lower() and 'derivative' not in str(c).lower():
            y1_col = c
        elif 'd.w' in str(c).lower() or 'derivative' in str(c).lower() or 'dtg' in str(c).lower():
            y2_col = c
            
    if x_col is None or y1_col is None or y2_col is None:
        continue
        
    temp = df[x_col].values
    weight = df[y1_col].values
    dtg = df[y2_col].values
    
    fig, ax1 = plt.subplots(figsize=(8, 6))
    
    color1 = '#1f4e9c'
    color2 = '#c0392b'
    
    ax1.set_xlabel('온도 (°C)', fontsize=12)
    ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
    ax1.plot(temp, weight, color=color1, label='Weight')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
    # Multiply DTG by -1 so peaks point up
    ax2.plot(temp, -dtg, color=color2, label='DTG')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title(sheet_name, fontsize=14)
    
    # Find Residue at ~800°C
    mask_800 = (temp >= 795) & (temp <= 805)
    if not np.any(mask_800):
         # If no data near 800, find closest
         idx_closest = np.argmin(np.abs(temp - 800))
         residue_val = weight[idx_closest]
         residue_temp = temp[idx_closest]
    else:
        # Average of points near 800
        residue_val = np.mean(weight[mask_800])
        residue_temp = 800.0
        
    # Find Peak above 150°C
    mask_peak = temp > 150
    if np.any(mask_peak):
        dtg_for_peak = -dtg[mask_peak] # Use inverted DTG for peak finding
        temp_for_peak = temp[mask_peak]
        
        max_idx_local = np.argmax(dtg_for_peak)
        peak_temp = temp_for_peak[max_idx_local]
        peak_dtg_val = dtg_for_peak[max_idx_local]
        
        # Plot markers
        ax1.scatter([residue_temp], [residue_val], color=color1, zorder=5)
        ax1.annotate(f'Residue {residue_val:.1f}%', 
                     xy=(residue_temp, residue_val), 
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=10, color=color1)
                     
        ax2.scatter([peak_temp], [peak_dtg_val], color=color2, zorder=5)
        ax2.annotate(f'{peak_temp:.0f} °C', 
                     xy=(peak_temp, peak_dtg_val), 
                     xytext=(10, 10), textcoords='offset points',
                     fontsize=10, color=color2)
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')
    
    plt.tight_layout()
    
    safe_sheet_name = "".join([i if i.isalnum() or i in ['-', '_'] else '_' for i in sheet_name])
    out_path = os.path.join(OUT_DIR, f"{safe_sheet_name}.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
