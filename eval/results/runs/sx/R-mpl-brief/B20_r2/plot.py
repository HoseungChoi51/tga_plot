import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B20_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet
sheet_name = "Acid-washed"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name, header=0)

# Extract columns based on preview info
# Columns: Time (min), Temperature (°C), Weight (%), Deriv. Weight (%/°C)
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
dtg_col = "Deriv. Weight (%/°C)"

x = df[temp_col].values
y1 = df[weight_col].values
y2_raw = df[dtg_col].values
y2 = -y2_raw  # Invert DTG so peaks point up

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
color1 = '#1f4e9c'
ax1.plot(x, y1, color=color1, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(False)

# Add minor ticks to x-axis
ax1.xaxis.set_minor_locator(mtick.AutoMinorLocator())
ax1.tick_params(which='minor', length=4, color='k')

# Create right y-axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.plot(x, y2, color=color2, linestyle='--', label='DTG (-dW/dT)')
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Find Residue at ~800°C
mask_800 = np.abs(x - 800) < 5  # Find points near 800°C
if not mask_800.any():
    idx_residue = np.argmin(np.abs(x - 800))
else:
    # Average or take closest? Standard is usually closest measured point.
    idx_residue = np.argmin(np.abs(x[mask_800] - 800))
    # Get actual index in original array
    indices = np.where(mask_800)[0]
    idx_residue = indices[np.argmin(np.abs(x[indices] - 800))]

residue_val = y1[idx_residue]
residue_temp = x[idx_residue]

# Find Peak DTG above 150°C
mask_peak = x > 150
if mask_peak.any():
    y2_masked = y2.copy()
    y2_masked[~mask_peak] = -np.inf
    idx_peak = np.argmax(y2_masked)
    peak_temp = x[idx_peak]
    peak_val = y2[idx_peak]
else:
    peak_temp = None
    peak_val = None

# Plot markers and labels for residue
ax1.plot(residue_temp, residue_val, 'o', color=color1, markersize=6)
ax1.annotate(f'Residue {residue_val:.1f}%', 
             xy=(residue_temp, residue_val), 
             xytext=(residue_temp + 20, residue_val + 5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=10, color='black')

# Plot markers and labels for peak
if peak_temp is not None:
    ax2.plot(peak_temp, peak_val, 'v', color=color2, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_val), 
                 xytext=(peak_temp + 20, peak_val * 0.9), # Adjust text position relative to right axis scale if needed, but simple offset works often
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
                 fontsize=10, color='black')

# Title
ax1.set_title(sheet_name, fontsize=14, fontweight='bold')

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', bbox_to_anchor=(0.05, 0.5))

plt.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, f"{sheet_name.replace(' ', '_')}.png")
plt.savefig(out_path, dpi=300)
plt.close()
