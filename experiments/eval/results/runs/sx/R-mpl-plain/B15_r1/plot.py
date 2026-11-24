import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B15_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

sheets = ['PE', 'PVC', 'PET']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

for i, sheet in enumerate(sheets):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    temp = df['Temperature (°C)']
    weight = df['Weight (%)']
    deriv_weight = df['Deriv. Weight (%/°C)']
    
    ax1.plot(temp, weight, color=colors[i], label=sheet, linewidth=1.5)
    ax2.plot(temp, deriv_weight, color=colors[i], label=sheet, linewidth=1.5)

ax1.set_ylabel('Weight (%)')
ax1.legend(loc='upper right', bbox_to_anchor=(1.15, 1), title='Polymer')
ax1.grid(True, linestyle='--', alpha=0.6)

ax2.set_xlabel('Temperature (°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)')
ax2.grid(True, linestyle='--', alpha=0.6)

fig.suptitle('TGA Data for PE, PVC, PET', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'tga_combined.png'), dpi=300, bbox_inches='tight')
plt.close()
