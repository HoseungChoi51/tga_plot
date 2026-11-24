import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILES = ["/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_A.csv", "/home/chs/Work/tga_plot/eval/inputs_b/cnt_lot_B.txt"]
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B05_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

fig, ax1 = plt.subplots(figsize=(8, 6))

colors = ['#1f4e9c', '#2ca02c']  # Blue for Lot A, Green for Lot B
labels = ['Lot A', 'Lot B']

for i, file_path in enumerate(DATA_FILES):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.txt'):
        df = pd.read_csv(file_path, sep=r'\s+')
    else:
        continue
    
    # Robust column selection based on preview info structure or fuzzy matching
    cols = df.columns.tolist()
    
    # Find Temperature column (usually contains 'Temp')
    temp_col = next((c for c in cols if 'temp' in c.lower()), None)
    # Find Weight column (usually contains 'Weight')
    weight_col = next((c for c in cols if 'weight' in c.lower() and 'deriv' not in c.lower()), None)
    # Find Deriv Weight column
    dtg_col = next((c for c in cols if 'deriv' in c.lower() or 'dtg' in c.lower()), None)
    
    if temp_col is None or weight_col is None or dtg_col is None:
        # Fallback to positional if names don't match expected patterns, though preview suggests they should
        # Based on preview: Col B=Temp, Col C=Weight, Col D=Deriv
        temp = df.iloc[:, 1].values
        weight = df.iloc[:, 2].values
        dtg = df.iloc[:, 3].values
    else:
        temp = df[temp_col].values
        weight = df[weight_col].values
        dtg = df[dtg_col].values
        
    # Plot Weight on left axis
    ax1.plot(temp, weight, color=colors[i], label=labels[i], linewidth=1.5)
    
    # Create right axis for DTG only once if needed, but we are looping. 
    # Better approach: Loop twice or collect data first. Let's collect data first to avoid twin axis issues in loop.
    pass

# Refactored approach: Collect all data first
data_list = []
for i, file_path in enumerate(DATA_FILES):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.txt'):
        df = pd.read_csv(file_path, sep=r'\s+')
    else:
        continue
        
    cols = df.columns.tolist()
    temp_col = next((c for c in cols if 'temp' in c.lower()), None)
    weight_col = next((c for c in cols if 'weight' in c.lower() and 'deriv' not in c.lower()), None)
    dtg_col = next((c for c in cols if 'deriv' in c.lower() or 'dtg' in c.lower()), None)
    
    if temp_col and weight_col and dtg_col:
        t = df[temp_col].values
        w = df[weight_col].values
        d = df[dtg_col].values
    else:
        t = df.iloc[:, 1].values
        w = df.iloc[:, 2].values
        d = df.iloc[:, 3].values
        
    data_list.append({'t': t, 'w': w, 'd': d, 'label': labels[i], 'color': colors[i]})

# Now plot
ax1 = fig.add_subplot(111)
ax2 = ax1.twinx()

for data in data_list:
    t = data['t']
    w = data['w']
    d = data['d']
    lbl = data['label']
    col = data['color']
    
    # Left Axis: Weight
    ax1.plot(t, w, color=col, label=lbl, linewidth=1.5)
    
    # Right Axis: -DTG
    ax2.plot(t, -d, color=col, linestyle='--', linewidth=1.0, alpha=0.7)
    
    # Annotations
    # Residue at ~800C
    idx_800 = np.argmin(np.abs(t - 800))
    res_val = w[idx_800]
    ax1.scatter([t[idx_800]], [res_val], color=col, s=30, zorder=5)
    ax1.text(t[idx_800], res_val, f'{res_val:.1f}%', fontsize=8, color=col, ha='center', va='bottom',
             bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
             
    # Peak above 150C
    mask = t > 150
    if np.any(mask):
        t_m = t[mask]
        d_m = d[mask]
        # Min DTG (most negative) corresponds to max -DTG peak
        peak_idx_local = np.argmin(d_m)
        peak_t = t_m[peak_idx_local]
        peak_d_val = d_m[peak_idx_local]
        
        # Marker on DTG curve (right axis)
        ax2.scatter([peak_t], [-peak_d_val], color=col, s=30, marker='v', zorder=5)
        ax2.text(peak_t, -peak_d_val, f'{peak_t:.0f}°C', fontsize=8, color=col, ha='center', va='bottom',
                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

# Labels and Limits
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', fontsize=12)
ax2.set_ylabel('-DTG (%/°C)', fontsize=12)

# Combine legends
lines1, labels1 = ax1.get_legend_handles_labels()
ax1.legend(lines1, labels1, loc='center left', fontsize=10)

ax1.set_title('TGA Overlay: Lot A vs Lot B', fontsize=14)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, 'overlay_tga.png')
plt.savefig(out_path, dpi=300)
plt.close()
