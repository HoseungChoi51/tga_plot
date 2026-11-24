import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B08_r2/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read only the "Raw" sheet
df = pd.read_excel(DATA_FILE, sheet_name="Raw", header=0)

temp = df["Temperature (°C)"].values
weight = df["Weight (%)"].values
dtg = df["Deriv. Weight (%/°C)"].values

fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot weight on left y-axis
color_y1 = '#1f4e9c'
ax1.plot(temp, weight, color=color_y1, label='Weight')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_y1)

# Horizontal reference line at 50% weight
ax1.axhline(y=50, color='gray', linestyle='--', linewidth=1, label='50%')

# Find residue at ~800°C
idx_800 = np.argmin(np.abs(temp - 800))
residue_val = weight[idx_800]
residue_temp = temp[idx_800]

# Mark residue point
ax1.plot(residue_temp, residue_val, 'o', color=color_y1, markersize=6)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val),
             xytext=(residue_temp + 30, residue_val + 5),
             fontsize=10, color=color_y1,
             arrowprops=dict(arrowstyle='->', color=color_y1))

# Create second y-axis for DTG
ax2 = ax1.twinx()
color_y2 = '#c0392b'
# Multiply DTG by -1 so peaks point up
dtg_inv = -dtg
ax2.plot(temp, dtg_inv, color=color_y2, label='DTG')
ax2.set_ylabel('DTG (-%/°C)', color=color_y2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color_y2)

# Find highest DTG peak above 150°C
mask = temp > 150
if mask.any():
    dtg_inv_masked = dtg_inv[mask]
    temp_masked = temp[mask]
    max_idx = np.argmax(dtg_inv_masked)
    peak_temp = temp_masked[max_idx]
    peak_dtg = dtg_inv_masked[max_idx]
    
    # Mark peak on DTG curve (on right axis)
    ax2.plot(peak_temp, peak_dtg, 'o', color=color_y2, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_dtg),
                 xytext=(peak_temp + 30, peak_dtg + 0.1),
                 fontsize=10, color=color_y2,
                 arrowprops=dict(arrowstyle='->', color=color_y2))

# Title from sheet name
ax1.set_title('Raw', fontsize=14)

# Legend at center left
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', fontsize=10)

# Add note in upper right corner
ax1.text(0.98, 0.95, '공기, 10 °C/min', transform=ax1.transAxes,
         fontsize=11, verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.5))

plt.tight_layout()
out_path = Path(OUT_DIR) / "Raw.png"
plt.savefig(out_path, dpi=300)
plt.close()
