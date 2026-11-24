import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/14_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read data with encoding handling
try:
    df = pd.read_csv(DATA_FILE, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(DATA_FILE, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_FILE, encoding='latin1')

# Identify columns based on the preview and standard TGA structure
# Columns: 시간(분), 온도(°C), 무게(%), 미분무게(%/°C)
x_col = "온도(°C)"
y1_col = "무게(%)"
y2_col = "미분무게(%/°C)"

# Extract data
temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Prepare plot
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (left axis)
color1 = '#1f4e9c'
ax1.plot(temp, weight, color=color1, label='무게 (%)')
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Plot DTG (right axis, inverted so peaks point up)
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(temp, -dtg, color=color2, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Find Residue at ~800°C
mask_800 = np.abs(temp - 800) < 5  # Look within +/- 5 degrees
if np.any(mask_800):
    idx_residue = np.argmin(np.abs(temp[mask_800] - 800))
    temp_residue = temp[mask_800][idx_residue]
    weight_residue = weight[mask_800][idx_residue]
else:
    # Fallback to closest overall if no data near 800
    idx_residue = np.argmin(np.abs(temp - 800))
    temp_residue = temp[idx_residue]
    weight_residue = weight[idx_residue]

# Mark residue
ax1.plot(temp_residue, weight_residue, 'o', color=color1, markersize=8)
ax1.annotate(f'Residue {weight_residue:.1f}%', 
             xy=(temp_residue, weight_residue), 
             xytext=(temp_residue + 50, weight_residue + 5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=10, color=color1)

# Find Peak temperature for DTG above 150°C
mask_peak = temp > 150
if np.any(mask_peak):
    dtg_subset = dtg[mask_peak]
    temp_subset = temp[mask_peak]
    # Since we plotted -dtg, the highest peak in the plot corresponds to the minimum of original dtg (most negative)
    # Or simply find the max of (-dtg) which is min(dtg)
    idx_peak_rel = np.argmin(dtg_subset) 
    temp_peak = temp_subset[idx_peak_rel]
    
    # Get actual values from original arrays for plotting consistency
    # We need the index in the original array corresponding to this subset index
    # Easier way: filter indices directly
    valid_indices = np.where(temp > 150)[0]
    if len(valid_indices) > 0:
        dtg_valid = dtg[valid_indices]
        best_idx_in_valid = np.argmin(dtg_valid) # Most negative value -> Highest peak when inverted
        global_idx = valid_indices[best_idx_in_valid]
        temp_peak_val = temp[global_idx]
        
        # Mark peak on DTG curve (which is -dtg on ax2)
        ax2.plot(temp_peak_val, -dtg[global_idx], 'v', color=color2, markersize=8)
        ax2.annotate(f'{temp_peak_val:.0f} °C', 
                     xy=(temp_peak_val, -dtg[global_idx]), 
                     xytext=(temp_peak_val + 50, -dtg[global_idx] + 0.1),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
                     fontsize=10, color=color2)

# Title
sheet_name = os.path.splitext(os.path.basename(DATA_FILE))[0]
plt.title(sheet_name, fontsize=14)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left')

plt.tight_layout()

# Save as PNG
png_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
plt.savefig(png_path, dpi=300)

# Save as PDF
pdf_path = os.path.join(OUT_DIR, f"{sheet_name}.pdf")
plt.savefig(pdf_path, format='pdf')

plt.close()
