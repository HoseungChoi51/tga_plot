import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/21_r3/out"

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

# Read the Excel file with header row 8 (0-indexed: row 7 in pandas read_excel skiprows=7)
df = pd.read_excel(DATA_FILE, sheet_name="Sheet1", header=None, skiprows=7)

# The first row after skipping should be the header
header_row = df.iloc[0].tolist()
data = df.iloc[1:].reset_index(drop=True)

# Assign column names based on the preview: B=Time, C=Temperature, D=Weight(%), E=D.W(%/C)
# In the dataframe read without header, columns are 0,1,2,3,...
# Column B is index 1, C is index 2, D is index 3, E is index 4
col_time = data.columns[1]   # B - Time
col_temp = data.columns[2]   # C - Temperature
col_weight = data.columns[3] # D - Weight(%)
col_dtg = data.columns[4]    # E - D.W(%/C)

# Extract data
temperature = data[col_temp].astype(float).values
weight = data[col_weight].astype(float).values
dtg = data[col_dtg].astype(float).values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot weight on left y-axis (y1)
color1 = '#1f4e9c'
ax1.plot(temperature, weight, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Create right y-axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
# Multiply DTG by -1 so peaks point up
dtg_negated = -dtg
ax2.plot(temperature, dtg_negated, color=color2, label='DTG (%/°C)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Find residue at ~800°C
idx_800 = np.argmin(np.abs(temperature - 800))
residue_val = weight[idx_800]
temp_at_residue = temperature[idx_800]

# Add residue marker and label
ax1.plot(temp_at_residue, residue_val, 'o', color=color1, markersize=6)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(temp_at_residue, residue_val),
             xytext=(10, -15), textcoords='offset points',
             fontsize=10, color=color1)

# Find highest DTG peak above 150°C
mask_above_150 = temperature > 150
if np.any(mask_above_150):
    dtg_for_peak = dtg[mask_above_150]
    temp_for_peak = temperature[mask_above_150]
    idx_max = np.argmax(dtg_for_peak)  # max of original DTG (most negative becomes smallest, but we want highest magnitude loss)
    # Actually, DTG is negative during mass loss. The "highest peak" in terms of mass loss rate means most negative DTG value.
    # But typically "peak" refers to the maximum of -DTG or minimum of DTG. Let's find the minimum of DTG (most negative) which corresponds to fastest mass loss.
    min_idx = np.argmin(dtg_for_peak)
    peak_temp = temp_for_peak[min_idx]
    peak_dtg_original = dtg_for_peak[min_idx]
    
    # Marker on the DTG curve (which is plotted as -DTG, so the y-value is -peak_dtg_original)
    ax2.plot(peak_temp, -peak_dtg_original, 'o', color=color2, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, -peak_dtg_original),
                 xytext=(10, 10), textcoords='offset points',
                 fontsize=10, color=color2)

# Title from sheet name
sheet_name = "Sheet1"
ax1.set_title(sheet_name, fontsize=14)

# Legend at center left
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
all_lines = lines1 + lines2
all_labels = labels1 + labels2
legend = ax1.legend(all_lines, all_labels, loc='center left', bbox_to_anchor=(0.05, 0.5))

# Save figure
output_path = Path(OUT_DIR) / f"{sheet_name}.png"
plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
