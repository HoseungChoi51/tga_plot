import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/extra_columns.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/24_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
df = pd.read_excel(DATA_FILE, sheet_name="CNT-01")

# Extract columns based on preview info
# Temperature (°C) is column B, Weight (%) is column E, Heat Flow (W/g) is column F
temp_col = "Temperature (°C)"
weight_col = "Weight (%)"
heat_flow_col = "Heat Flow (W/g)"

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot TGA (Weight %) on primary y-axis
ax1.plot(df[temp_col], df[weight_col], color='blue', label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')

# Create secondary y-axis for Heat Flow
ax2 = ax1.twinx()
ax2.plot(df[temp_col], df[heat_flow_col], color='red', linestyle='--', label='Heat flow (W/g)')
ax2.set_ylabel('Heat flow (W/g)', color='red', fontsize=12)
ax2.tick_params(axis='y', labelcolor='red')

# Title
plt.title('TGA and DSC Analysis of CNT-01', fontsize=14)

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save plot
output_path = os.path.join(OUT_DIR, "tga_heatflow.png")
plt.savefig(output_path, dpi=300)
plt.close()
