import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/instrument_export.txt"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/23_r1/out"

# Read the data file with encoding='latin-1' to handle potential non-UTF8 characters in header/metadata
df = pd.read_csv(DATA_FILE, sep='\t', skiprows=10, header=None, names=['A', 'B', 'C', 'D'], encoding='latin-1')

# Extract columns based on TGA guess: x=B, y1=C (Weight %), y2=D (DTG or similar)
# Convert to numeric to ensure they are treated as numbers, not categories
x_data = pd.to_numeric(df['B'], errors='coerce').dropna().values
y_weight = pd.to_numeric(df['C'], errors='coerce').dropna().values
y_dtg = pd.to_numeric(df['D'], errors='coerce').dropna().values

# Ensure arrays are same length after dropping NaNs
min_len = min(len(x_data), len(y_weight), len(y_dtg))
x_data = x_data[:min_len]
y_weight = y_weight[:min_len]
y_dtg = y_dtg[:min_len]

# Create figure with two subplots sharing x-axis
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Plot Weight (%) vs Temperature
ax1.plot(x_data, y_weight, color='blue', label='Weight (%)')
ax1.set_ylabel('Weight (%)')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend()

# Add residue annotation
# Find the final weight value (last point)
if len(y_weight) > 0:
    final_weight = y_weight[-1]
    residue_text = f'Residue: {final_weight:.2f}%'
    ax1.text(0.95, 0.05, residue_text, transform=ax1.transAxes, fontsize=12,
             verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

# Plot DTG vs Temperature
ax2.plot(x_data, y_dtg, color='red', label='DTG (%/°C)')
ax2.set_xlabel('Temperature (°C)')
ax2.set_ylabel('DTG (%/°C)')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

plt.tight_layout()

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Save the plot
output_path = os.path.join(OUT_DIR, 'tga_plot.png')
plt.savefig(output_path, dpi=300)
plt.close()
