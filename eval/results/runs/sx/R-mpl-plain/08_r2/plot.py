import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/08_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets from the Excel file
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Identify columns based on the preview info
    # Columns: Time, Temperature, Weight(%), D.W(%/C)
    temp_col = 'Temperature'
    weight_col = 'Weight(%)'
    dw_col = 'D.W(%/C)'
    
    x = df[temp_col]
    y1 = df[weight_col]
    y2 = df[dw_col]
    
    color = colors[i % len(colors)]
    
    # Plot Weight (%) on primary axis (left)
    line1, = ax1.plot(x, y1, label=f'{sheet_name} - 무게 (%)', color=color, linestyle='-')
    
    # Create secondary axis for D.W (%/C)
    ax2 = ax1.twinx()
    line2, = ax2.plot(x, y2, label=f'{sheet_name} - 미분 무게 (%/°C)', color=color, linestyle='--', alpha=0.7)

# Set labels with requested text
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', fontsize=12, color='black')
ax2.set_ylabel('미분 무게 (%/°C)', fontsize=12, color='black')

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='best', fontsize=9)

ax1.grid(True, linestyle=':', alpha=0.5)
plt.title('TGA 결과 비교', fontsize=14)

out_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.tight_layout()
plt.savefig(out_path, dpi=300)
plt.close()
