import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B17_r2/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read all sheets
xls = pd.ExcelFile(DATA_FILE)
sheet_names = xls.sheet_names

fig, ax = plt.subplots(figsize=(8, 6))

colors = ['#1f4e9c', '#c0392b', '#2ecc71']
offset_step = 20

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    
    # Identify columns based on the preview info
    temp_col = None
    weight_col = None
    
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight (%)' in str(col) or (col == 'C' and '%' in str(df[col].iloc[0]) if not df.empty else False):
            weight_col = col
            
    # Fallback to positional if names don't match exactly but structure is known from preview
    if temp_col is None:
        temp_col = df.columns[1] # Column B
    if weight_col is None:
        weight_col = df.columns[2] # Column C
        
    x = df[temp_col].values
    y = df[weight_col].values
    
    # Apply offset: shift each curve up by 20% * index
    # To keep them visible and non-overlapping, we add an increasing offset
    # Since weight starts at 100%, shifting up makes sense to separate them visually
    # Or we can just plot them with offsets relative to a baseline. 
    # The request says "overlap avoidance by 20% vertical offset".
    # Usually this means adding a constant value to Y for each subsequent series.
    y_offset = y + (i * offset_step)
    
    ax.plot(x, y_offset, label=f"{sheet_name} (+{i*offset_step}%)", color=colors[i % len(colors)], linewidth=1.5)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA Weight Curves with Vertical Offsets")
ax.legend(loc='center left')
ax.grid(True, linestyle='--', alpha=0.5)

out_path = Path(OUT_DIR) / "polymers_offsets.png"
plt.tight_layout()
plt.savefig(out_path, dpi=300)
plt.close()
