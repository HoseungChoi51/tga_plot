import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/18_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
labels = []

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Identify columns based on the preview info
    temp_col = None
    weight_col = None
    dw_col = None
    
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight' in str(col):
            weight_col = col
        elif 'D.W' in str(col) or 'DW' in str(col):
            dw_col = col
            
    if temp_col is None or weight_col is None or dw_col is None:
        continue
        
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dw_col]
    
    # Plot Weight (%) on primary axis (left)
    color1 = colors[i % len(colors)]
    line1, = ax1.plot(x, y1, color=color1, label=f'{sheet_name} - Weight(%)')
    
    # Plot D.W (%/C) on secondary axis (right)
    ax2 = ax1.twinx()
    line2, = ax2.plot(x, y2, color=color1, linestyle='--', alpha=0.7, label=f'{sheet_name} - D.W(%/C)')
    
    labels.append((line1, line2))

# Configure X-axis
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_xlim(30, 900)
ax1.set_xticks(np.arange(0, 901, 100))

# Configure Y1-axis (Weight %)
ax1.set_ylabel('Weight (%)', fontsize=12, color='black')
ax1.tick_params(axis='y', labelcolor='black')

# Configure Y2-axis (D.W %/C)
ax2 = ax1.twinx()
ax2.set_ylabel('Derivative Weight (%/°C)', fontsize=12, color='black')
ax2.set_ylim(-0.05, 1.2)
ax2.tick_params(axis='y', labelcolor='black')

# Combine legends from both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', bbox_to_anchor=(1.0, 0.5), fontsize=9)

ax1.grid(True, linestyle=':', alpha=0.5)
plt.title('TGA Curves', fontsize=14)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
