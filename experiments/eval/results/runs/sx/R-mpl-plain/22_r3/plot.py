import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/22_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

sheets = [
    "1006R1-V normal",
    "1006R1-V acid",
    "1006R1-V 750C"
]

fig, axes = plt.subplots(len(sheets), 1, figsize=(10, 12))
if len(sheets) == 1:
    axes = [axes]

for ax, sheet_name in zip(axes, sheets):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)
    
    # Identify columns based on the preview info
    x_col = "Temperature"
    y1_col = "Weight(%)"
    y2_col = "D.W(%/C)"
    
    temp = df[x_col].values
    weight = df[y1_col].values
    dwt = df[y2_col].values
    
    # Plot TGA (Weight %) on primary axis
    line1 = ax.plot(temp, weight, color='blue', label='Weight (%)')
    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('Weight (%)', color='blue', fontsize=12)
    ax.tick_params(axis='y', labelcolor='blue')
    
    # Create secondary axis for DTG
    ax2 = ax.twinx()
    # Plot DTG on secondary axis with green color
    line2 = ax2.plot(temp, dwt, color='green', linestyle='--', label='DTG (%/°C)')
    ax2.set_ylabel('DTG (%/°C)', color='green', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='green')
    
    # Title
    ax.set_title(f'TGA/DTG - {sheet_name}', fontsize=14)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc='upper right')
    
    ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_plots.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
