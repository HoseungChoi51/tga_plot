import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B17_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax = plt.subplots(figsize=(8, 6))

offset_step = 20  # 20% offset between curves

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on the preview
    temp_col = None
    weight_col = None
    
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight' in str(col) and 'Deriv' not in str(col):
            weight_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    x = df[temp_col].values
    y = df[weight_col].values
    
    # Apply offset: first curve at 0, second at +20, third at +40, etc.
    # Or we can shift them so they don't overlap visually. 
    # Usually offsets are added to separate them. Let's add i * offset_step.
    y_offset = y + (i * offset_step)
    
    ax.plot(x, y_offset, label=sheet_name)

ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Weight (%) with Offset')
ax.legend(loc='best')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

out_path = os.path.join(OUT_DIR, "polymers_offset.png")
plt.savefig(out_path, dpi=300)
plt.close()
