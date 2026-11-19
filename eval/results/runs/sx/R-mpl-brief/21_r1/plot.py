import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/21_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the Excel file with header at row 8 (0-indexed row 7 in pandas if we skiprows=7 and use header=0? 
# The preview says header_rows: [8], data_start_row: 9. In openpyxl/pandas terms, this usually means 
# row index 7 is the header if we consider 1-based indexing for rows in Excel vs 0-based in pandas read_excel.
# Let's try reading with skiprows=7 and header=0 to get columns starting from B, C, D, E.
# However, standard pandas read_excel with header=7 (0-indexed) might be safer if the first 7 rows are skipped.
# Actually, if header_rows is [8] in 1-based Excel notation, that corresponds to index 7 in 0-based Python.
df = pd.read_excel(DATA_FILE, sheet_name='Sheet1', skiprows=7, header=0)

# Clean column names if necessary (remove leading/trailing spaces)
df.columns = df.columns.str.strip()

# Identify columns based on user request: C->X, D->Y1, E->Y2
# From preview: Col C is "Temperature", Col D is "Weight(%)", Col E is "D.W(%/C)"
# We need to find these columns by name or position.
# Assuming the dataframe loaded correctly has these columns.
try:
    x_col = 'Temperature'
    y1_col = 'Weight(%)'
    y2_col = 'D.W(%/C)'
except KeyError:
    # Fallback to positional if names don't match exactly due to whitespace etc.
    # Based on preview: B=Time, C=Temp, D=Weight, E=DTG
    # If headers were read correctly, they should be there. 
    # If not, let's assume standard TGA structure after skipping rows.
    cols = df.columns.tolist()
    # Heuristic: find numeric columns
    x_col = cols[1] # C
    y1_col = cols[2] # D
    y2_col = cols[3] # E

# Extract data
x = df[x_col].values
y1 = df[y1_col].values
y2 = df[y2_col].values

# Create plot
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight (%) on left axis
color1 = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1, = ax1.plot(x, y1, color=color1, label='Weight')
ax1.tick_params(axis='y', labelcolor=color1)

# Create second axis sharing x-axis
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
# Multiply DTG by -1 so peaks point up
line2, = ax2.plot(x, -y2, color=color2, label='DTG')
ax2.tick_params(axis='y', labelcolor=color2)

# Title: Sheet Name
sheet_name = 'Sheet1'
plt.title(sheet_name, fontsize=14)

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

# Calculate Residue at ~800°C
idx_800 = np.argmin(np.abs(x - 800))
residue_val = y1[idx_800]
residue_temp = x[idx_800]
ax1.plot(residue_temp, residue_val, 'o', color=color1)
ax1.annotate(f'Residue {residue_val:.1f}%', xy=(residue_temp, residue_val), xytext=(10, 10), textcoords='offset points', ha='left', va='bottom', color=color1, fontsize=10)

# Calculate Peak Temperature of DTG above 150°C
mask = x > 150
if np.any(mask):
    dtg_masked = -y2[mask] # Use inverted DTG values
    temp_masked = x[mask]
    
    # Find max peak
    max_idx = np.argmax(dtg_masked)
    peak_temp = temp_masked[max_idx]
    peak_val_inv = dtg_masked[max_idx]
    peak_val_orig = -peak_val_inv
    
    # Plot marker on right axis
    ax2.plot(peak_temp, peak_val_inv, 'o', color=color2)
    ax2.annotate(f'{peak_temp:.0f} °C', xy=(peak_temp, peak_val_inv), xytext=(10, 10), textcoords='offset points', ha='left', va='bottom', color=color2, fontsize=10)

plt.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, f"{sheet_name}.png")
plt.savefig(out_path, dpi=300)
plt.close()
