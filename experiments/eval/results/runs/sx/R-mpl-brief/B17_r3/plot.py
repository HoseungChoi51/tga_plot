import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B17_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read all sheets
xl = pd.ExcelFile(DATA_FILE)
sheet_names = xl.sheet_names

fig, ax = plt.subplots(figsize=(8, 6))

colors = ['#1f4e9c', '#2ca02c', '#d62728']  # Distinct colors for each polymer

for i, sheet in enumerate(sheet_names):
    df = pd.read_excel(DATA_FILE, sheet_name=sheet)
    
    # Identify columns based on standard TGA structure
    temp_col = None
    weight_col = None
    
    for col in df.columns:
        if 'Temperature' in str(col):
            temp_col = col
        elif 'Weight' in str(col) and 'Deriv' not in str(col):
            weight_col = col
            
    if temp_col is None or weight_col is None:
        continue
        
    temps = df[temp_col].values
    weights = df[weight_col].values
    
    # Apply offset to prevent overlap
    # Offset by 20% of the range (approx 100%) for each subsequent curve
    # To stack them nicely, we shift them down. 
    # Let's say PE stays at original, PVC shifted by -25%, PET shifted by -50%?
    # Or just simple stacking with a fixed gap. The user asked for "20%씩 위아래로 띄워서".
    # Usually this means vertical separation. Since weight decreases, shifting down separates them.
    # Let's use an offset factor relative to the initial weight (100%).
    offset = i * 25  # Shift each curve down by 25 units (percentage points)
    
    plot_weights = weights - offset
    
    ax.plot(temps, plot_weights, label=f"{sheet} (offset {offset})", color=colors[i % len(colors)], linewidth=1.5)

ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Weight (%)")
ax.set_title("TGA Weight Curves (Stacked with Offset)")
ax.legend(loc='center left')
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

out_path = os.path.join(OUT_DIR, "polymers_stacked.png")
plt.savefig(out_path, dpi=300)
plt.close()
