import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B09_r3/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read the PE sheet from the Excel file
df_pe = pd.read_excel(DATA_FILE, sheet_name='PE')

# Extract columns based on the preview info
# x: Temperature (°C), y1: Weight (%), y2: Deriv. Weight (%/°C)
temp = df_pe['Temperature (°C)']
weight = df_pe['Weight (%)']
deriv_weight = df_pe['Deriv. Weight (%/°C)']

# Create the figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight (%) on the primary y-axis (left)
color1 = 'red'
ax1.plot(temp, weight, color=color1, linewidth=3, label='Weight (%)')
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)

# Set x-axis limits and ticks as requested
ax1.set_xlim(100, 700)
ax1.set_xticks(range(100, 800, 100)) # 100, 200, ..., 700

# Create a secondary y-axis for Derivative Weight
ax2 = ax1.twinx()
color2 = 'blue'
ax2.plot(temp, deriv_weight, color=color2, linewidth=1.5, linestyle='--', label='Deriv. Weight (%/°C)')
ax2.set_ylabel('Deriv. Weight (%/°C)', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)

# Add titles and legend
fig.suptitle('TGA Analysis of PE', fontsize=14)
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

# Adjust layout to prevent overlap
fig.tight_layout(rect=[0, 0, 1, 0.96])

# Save the plot
output_path = os.path.join(OUT_DIR, "PE_TGA.png")
plt.savefig(output_path, dpi=300)
plt.close()
