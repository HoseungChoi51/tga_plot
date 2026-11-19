import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B15_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()

colors_weight = ['#1f4e9c', '#27ae60', '#8e44ad']
colors_dtg = ['#c0392b', '#e67e22', '#2980b9']

legend_handles_1 = []
legend_handles_2 = []

for i, sheet in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    
    # Identify columns based on preview info
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and 'deriv' not in col_lower and 'derivative' not in col_lower:
            weight_col = col
        elif 'deriv' in col_lower or 'dtg' in col_lower:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    x = df[temp_col].values
    y1 = df[weight_col].values
    y2 = -df[dtg_col].values  # Multiply by -1 to make peaks point up
    
    c_w = colors_weight[i % len(colors_weight)]
    c_d = colors_dtg[i % len(colors_dtg)]
    
    line1, = ax1.plot(x, y1, color=c_w, label=f'{sheet} Weight (%)')
    line2, = ax2.plot(x, y2, color=c_d, linestyle='--', label=f'{sheet} DTG (-%/°C)')
    
    legend_handles_1.append(line1)
    legend_handles_2.append(line2)
    
    # Find residue at ~800°C
    idx_res = np.argmin(np.abs(x - 800))
    res_val = y1[idx_res]
    ax1.plot(x[idx_res], y1[idx_res], 'o', color=c_w, markersize=6)
    ax1.annotate(f'Residue {res_val:.1f}%', xy=(x[idx_res], y1[idx_res]), 
                 xytext=(x[idx_res]+20, y1[idx_res]-5), fontsize=8, color=c_w)
                 
    # Find peak temperature > 150°C
    mask = (x > 150) & (~np.isnan(y2))
    if np.any(mask):
        y2_masked = y2[mask]
        x_masked = x[mask]
        peak_idx = np.argmax(y2_masked)
        peak_temp = x_masked[peak_idx]
        peak_val = y2_masked[peak_idx]
        
        ax2.plot(peak_temp, peak_val, 'v', color=c_d, markersize=6)
        ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_val), 
                     xytext=(peak_temp+20, peak_val+0.2), fontsize=8, color=c_d)

ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Weight (%)')
ax2.set_ylabel('DTG (%/°C)')

# Combine handles for legend outside right
all_handles = legend_handles_1 + legend_handles_2
ax1.legend(all_handles, [h.get_label() for h in all_handles], loc='center left', bbox_to_anchor=(1.02, 0.5))

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "polymers_overlay.png"), dpi=300, bbox_inches='tight')
plt.close()
