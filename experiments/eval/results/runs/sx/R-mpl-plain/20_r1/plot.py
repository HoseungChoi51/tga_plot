import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/20_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheets = xls.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
linestyles = ['-', '--', '-.']

for i, sheet_name in enumerate(sheets):
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    # Clean column names if needed
    cols = df.columns.tolist()
    temp_col = None
    weight_col = None
    dw_col = None
    
    for c in cols:
        if 'temperature' in str(c).lower():
            temp_col = c
        elif 'weight' in str(c).lower() and '%' in str(c):
            weight_col = c
        elif 'd.w' in str(c).lower() or 'dw' in str(c).lower():
            dw_col = c
            
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col]
    y_weight = df[weight_col]
    
    # Plot Weight (%) on primary axis
    color = colors[i % len(colors)]
    ls = linestyles[i % len(linestyles)]
    line1, = ax1.plot(x, y_weight, label=f'{sheet_name} (Weight)', color=color, linestyle=ls, linewidth=1.5)
    
    # If D.W exists, plot on secondary axis
    if dw_col is not None:
        y_dw = df[dw_col]
        ax2 = ax1.twinx()
        line2, = ax2.plot(x, y_dw, label=f'{sheet_name} (D.W)', color=color, linestyle=':', linewidth=1.0, alpha=0.7)
        
        # Only create one twin axis instance logic is tricky in loop, 
        # better to handle axes outside or just plot weights for simplicity if multiple twins cause issues.
        # However, standard practice for TGA is TG on left, DTG on right.
        # Let's restructure slightly to ensure clean plotting.

# Redoing the plotting logic more robustly for multiple sheets with twin axes
ax1.clear()
ax1 = fig.add_subplot(111)

# We need a single twinx axis for all DTG plots
ax2 = ax1.twinx()

lines1 = []
labels1 = []
lines2 = []
labels2 = []

for i, sheet_name in enumerate(sheets):
    df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
    
    cols = df.columns.tolist()
    temp_col = next((c for c in cols if 'temperature' in str(c).lower()), None)
    weight_col = next((c for c in cols if 'weight' in str(c).lower() and '%' in str(c)), None)
    dw_col = next((c for c in cols if 'd.w' in str(c).lower() or 'dw' in str(c).lower()), None)
    
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col]
    y_weight = df[weight_col]
    
    color = colors[i % len(colors)]
    ls = linestyles[i % len(linestyles)]
    
    l1, = ax1.plot(x, y_weight, label=f'{sheet_name}', color=color, linestyle=ls, linewidth=1.5)
    lines1.append(l1)
    labels1.append(f'{sheet_name}')
    
    if dw_col is not None:
        y_dw = df[dw_col]
        l2, = ax2.plot(x, y_dw, color=color, linestyle=':', linewidth=1.0, alpha=0.6)
        lines2.append(l2)
        labels2.append(f'{sheet_name} (DTG)')

# Add shaded region 300~450 °C
ax1.axvspan(300, 450, color='gray', alpha=0.2, label='300-450 °C')

ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Weight (%)')
ax2.set_ylabel('Derivative Weight (%/°C)')

ax1.set_title('TGA/DTG Curves')

# Combine legends
l1, lab1 = ax1.get_legend_handles_labels()
l2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(l1 + l2, lab1 + lab2, loc='best', fontsize=8)

ax1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(out_path, dpi=300)
plt.close()
