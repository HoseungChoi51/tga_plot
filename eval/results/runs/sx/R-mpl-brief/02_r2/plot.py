import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/02_r2/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

sheet_name = "1006R1-V normal"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# Column names from preview: Time(A), Temperature(B), Weight(%)(C), D.W(%/C)(D)
# User says B행=X, C행=Y1, D행=Y2 -> Temperature, Weight(%), D.W(%/C)
x_col = df.columns[1]  # Temperature
y1_col = df.columns[2]  # Weight(%)
y2_col = df.columns[3]  # D.W(%/C)

x = df[x_col].values
y1 = df[y1_col].values
y2 = df[y2_col].values

fig, ax1 = plt.subplots(figsize=(8, 5))

# Y1: Weight (%) - left axis
color_y1 = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color_y1, fontsize=12)
line1, = ax1.plot(x, y1, color=color_y1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color_y1)
ax1.set_xlim(0, max(x.max(), 900))
ax1.set_xticks(np.arange(0, x.max() + 200, 200))

# Y2: Derivative Weight - right axis, multiplied by -1 so peaks point up
ax2 = ax1.twinx()
color_y2 = '#c0392b'
ax2.set_ylabel('Deriv. Weight (%/°C)', color=color_y2, fontsize=12)
line2, = ax2.plot(x, -y2, color=color_y2, label='Deriv. Weight (%/°C)')
ax2.tick_params(axis='y', labelcolor=color_y2)

# Find DTG peak above 150°C (highest of -y2 means most negative original y2)
mask_peak = x > 150
if mask_peak.any():
    idx_peak = np.argmax(-y2[mask_peak])
    peak_x = x[mask_peak][idx_peak]
    peak_y_neg = -y2[mask_peak][idx_peak]
    ax2.plot(peak_x, peak_y_neg, 'o', color=color_y2, markersize=8)
    ax2.annotate(f'{peak_x:.0f} °C', xy=(peak_x, peak_y_neg),
                 xytext=(peak_x + 30, peak_y_neg + 0.05),
                 fontsize=10, color=color_y2,
                 arrowprops=dict(arrowstyle='->', color=color_y2))

# Residue at nearest to 800°C
target_temp = 800
idx_residue = np.argmin(np.abs(x - target_temp))
residue_weight = y1[idx_residue]
residue_temp = x[idx_residue]
ax1.plot(residue_temp, residue_weight, 'o', color=color_y1, markersize=8)
ax1.annotate(f'Residue {residue_weight:.1f}%', xy=(residue_temp, residue_weight),
             xytext=(residue_temp - 100, residue_weight + 5),
             fontsize=10, color=color_y1,
             arrowprops=dict(arrowstyle='->', color=color_y1))

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', fontsize=10)

# Title
ax1.set_title(sheet_name, fontsize=14)

# Grid
ax1.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()

out_path = Path(OUT_DIR) / f"{sheet_name}.png"
fig.savefig(out_path, dpi=300)
plt.close(fig)
