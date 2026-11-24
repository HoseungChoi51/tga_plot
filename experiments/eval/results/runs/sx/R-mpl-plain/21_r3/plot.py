import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/blank_rows_on_top.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/21_r3/out"

# Read the Excel file with header at row 8 (0-indexed: 7)
df = pd.read_excel(DATA_FILE, sheet_name='Sheet1', header=7)

# Extract columns
x = df['Temperature']
y1 = df['Weight(%)']
y2 = df['D.W(%/C)']

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight(%) on primary Y-axis
ax1.plot(x, y1, color='blue', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# Create secondary Y-axis
ax2 = ax1.twinx()
ax2.plot(x, y2, color='red', label='D.W (%/°C)')
ax2.set_ylabel('D.W (%/°C)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# Add title
plt.title('TGA Curve', fontsize=14)

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

# Tight layout to prevent overlap
fig.tight_layout()

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Save figure
output_path = os.path.join(OUT_DIR, "tga_plot.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
