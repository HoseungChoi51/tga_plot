import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/09_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xl_file = pd.ExcelFile(DATA_FILE)
sheet_names = xl_file.sheet_names

fig, axes = plt.subplots(len(sheet_names), 1, figsize=(8, 4 * len(sheet_names)), sharex=False)

if len(sheet_names) == 1:
    axes = [axes]

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=1)
    
    # Identify columns based on the preview structure
    temp_col = None
    weight_col = None
    dtg_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'temperature' in col_str:
            temp_col = col
        elif 'weight' in col_str and '%' in col_str:
            weight_col = col
        elif 'd.w' in col_str or 'dtg' in col_str:
            dtg_col = col
            
    if temp_col is None or weight_col is None or dtg_col is None:
        continue
        
    ax = axes[i]
    ax_twin = ax.twinx()
    
    x_data = df[temp_col]
    y_weight = df[weight_col]
    y_dtg = df[dtg_col]
    
    # Plot Weight (%) on left axis
    line1, = ax.plot(x_data, y_weight, color=colors[i % len(colors)], label='Weight (%)')
    ax.set_ylabel('Weight (%)')
    ax.tick_params(axis='y', direction='out', labelsize=9)
    
    # Plot DTG on right axis
    line2, = ax_twin.plot(x_data, y_dtg, color='red', linestyle='--', label='DTG (%/°C)')
    ax_twin.set_ylabel('DTG (%/°C)')
    ax_twin.tick_params(axis='y', direction='out', labelsize=9)
    
    # X-axis settings
    ax.set_xlabel('Temperature (°C)')
    ax.tick_params(axis='x', direction='out', labelsize=9)
    
    # Title and Legend
    ax.set_title(f'TGA Analysis: {sheet_name}')
    
    # Combine legends
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='best')
    
    ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300)
plt.close()
