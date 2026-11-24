import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/01_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, axes = plt.subplots(len(sheet_names), 1, figsize=(10, 4 * len(sheet_names)), sharex=True)
if len(sheet_names) == 1:
    axes = [axes]

for ax, sheet_name in zip(axes, sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on preview info
    temp_col = None
    weight_col = None
    dw_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'temperature' in col_lower or 'temp' in col_lower:
            temp_col = col
        elif 'weight' in col_lower and '%' in col_lower:
            weight_col = col
        elif 'd.w' in col_lower or 'dw' in col_lower or 'derivative' in col_lower:
            dw_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col]
    y1 = df[weight_col]
    
    # Plot TGA (Weight %) on primary axis
    line1 = ax.plot(x, y1, color='blue', label=f'TGA ({sheet_name})')
    ax.set_ylabel('Weight (%)', color='blue')
    ax.tick_params(axis='y', labelcolor='blue')
    
    # Plot DTG (D.W %/C) on secondary axis if available
    if dw_col:
        y2 = df[dw_col]
        ax2 = ax.twinx()
        line2 = ax2.plot(x, y2, color='red', linestyle='--', label=f'DTG ({sheet_name})')
        ax2.set_ylabel('D.W (%/C)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper right')
    else:
        ax.legend(loc='upper right')
        
    ax.set_xlabel('Temperature (°C)')
    ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, "TGA_plots.png")
plt.savefig(out_path, dpi=300, bbox_inches='tight')
plt.close()
