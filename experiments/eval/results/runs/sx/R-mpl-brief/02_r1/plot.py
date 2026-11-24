import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/CNT/Plot/tests/inputs/TGA.xlsx"
OUT_DIR = "/home/chs/CNT/Plot/eval/results/runs/sx/R-mpl-brief/02_r1/out"
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read the specific sheet
sheet_name = "1006R1-V normal"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# Extract columns: B (Temperature), C (Weight%), D (D.W %/C)
temperature = df.iloc[:, 1].values  # Column B
weight = df.iloc[:, 2].values       # Column C
dtg = df.iloc[:, 3].values          # Column D

# Create figure with twin axes
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight on left y-axis
color1 = '#1f4e9c'
ax1.plot(temperature, weight, color=color1, linewidth=1.5, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Set x-axis ticks from 0 to max temperature in steps of 200
max_temp = np.max(temperature)
x_ticks = np.arange(0, int(max_temp) + 200, 200)
ax1.set_xticks(x_ticks)
ax1.set_xlim(left=0)

# Set y1 ticks in steps of 20
y1_min = np.min(weight)
y1_max = np.max(weight)
y1_ticks = np.arange(np.floor(y1_min / 20) * 20, np.ceil(y1_max / 20) * 20 + 20, 20)
ax1.set_yticks(y1_ticks)

# Create twin axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
# Multiply DTG by -1 so peaks point up
dtg_inverted = dtg * -1
ax2.plot(temperature, dtg_inverted, color=color2, linewidth=1.5, label='DTG (%/°C)')
ax2.set_ylabel('Derivative Weight (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Set y2 ticks in steps of 0.2
y2_min = np.min(dtg_inverted)
y2_max = np.max(dtg_inverted)
y2_ticks = np.arange(np.floor(y2_min / 0.2) * 0.2, np.ceil(y2_max / 0.2) * 0.2 + 0.2, 0.2)
ax2.set_yticks(y2_ticks)

# Find and mark the DTG peak above 150°C
mask_above_150 = temperature > 150
if np.any(mask_above_150):
    dtg_above_150 = dtg[mask_above_150]
    temp_above_150 = temperature[mask_above_150]
    
    # Find index of maximum DTG (most negative value, since we inverted it becomes highest positive)
    # Actually, DTG is negative during mass loss. The "peak" is where |DTG| is largest.
    # In original data, find minimum DTG (most negative) above 150°C
    idx_min_dtg = np.argmin(dtg_above_150)
    peak_temp = temp_above_150[idx_min_dtg]
    peak_weight = weight[mask_above_150][idx_min_dtg]
    
    # Mark peak on the plot
    ax1.axvline(x=peak_temp, color='gray', linestyle='--', alpha=0.5)
    ax1.scatter([peak_temp], [peak_weight], color='red', zorder=5, s=50)
    ax1.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_weight), 
                 xytext=(peak_temp + 30, peak_weight + 5),
                 arrowprops=dict(arrowstyle='->', color='black'),
                 fontsize=10, color='black')

# Find residue at temperature nearest to 800°C
idx_nearest_800 = np.argmin(np.abs(temperature - 800))
residue_temp = temperature[idx_nearest_800]
residue_weight = weight[idx_nearest_800]

# Mark residue
ax1.scatter([residue_temp], [residue_weight], color='green', zorder=5, s=50, marker='o')
ax1.annotate(f'Residue {residue_weight:.1f}%', xy=(residue_temp, residue_weight),
             xytext=(residue_temp - 150, residue_weight + 10),
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=10, color='black')

# Title
ax1.set_title(sheet_name, fontsize=14, fontweight='bold')

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.02, 0.5))

# Grid
ax1.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()

# Save figure
output_path = Path(OUT_DIR) / f"{sheet_name.replace(' ', '_').replace('/', '_')}.png"
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
