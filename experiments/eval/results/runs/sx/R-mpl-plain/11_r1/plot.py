import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/11_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Clean column names just in case they have extra spaces
    cols = [str(c).strip() for c in df.columns]
    df.columns = cols
    
    temp_col = None
    weight_col = None
    dw_col = None
    
    for c in cols:
        if 'Temperature' in c:
            temp_col = c
        elif 'Weight' in c and '%' in c:
            weight_col = c
        elif 'D.W' in c or 'DTG' in c or ('W' in c and '%' in c and 'C' in c):
            dw_col = c
            
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col].dropna().values
    y_weight = df[weight_col].dropna().values
    
    # Plot Weight % on primary axis
    color = colors[i % len(colors)]
    line1, = ax1.plot(x, y_weight, label=f'{sheet_name} (TGA)', color=color, linewidth=1.5)
    
    # If DTG/D.W exists, plot on secondary axis
    if dw_col:
        y_dw = df[dw_col].dropna().values
        # Align lengths just in case of NaNs causing mismatch
        min_len = min(len(x), len(y_dw))
        ax2 = ax1.twinx()
        line2, = ax2.plot(x[:min_len], y_dw[:min_len], linestyle='--', color=color, alpha=0.6, linewidth=1.0, label=f'{sheet_name} (DTG)')
        
        # Add secondary axis label only once to avoid clutter, or per dataset? 
        # Usually shared secondary axis is better. We'll set the label after loop or use a generic one.
        # For now, we rely on legend to distinguish TGA vs DTG lines.

ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax1.tick_params(axis='y', labelcolor='#333333')

if 'ax2' in locals():
    ax2.set_ylabel('Derivative Weight (%/°C)', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#666666')

# Combine legends from both axes if ax2 exists
lines_labels = ax1.get_legend_handles_labels()
if 'ax2' in locals():
    lines_labels2 = ax2.get_legend_handles_labels()
    lines = lines_labels[0] + lines_labels2[0]
    labels = lines_labels[1] + lines_labels2[1]
else:
    lines = lines_labels[0]
    labels = lines_labels[1]

ax1.legend(lines, labels, loc='best', fontsize=9)
ax1.grid(True, linestyle=':', alpha=0.6)

plt.title('TGA/DTG Curves Comparison', fontsize=14)
plt.tight_layout()

output_path = os.path.join(OUT_DIR, "tga_comparison.png")
plt.savefig(output_path, dpi=300)
plt.close()
