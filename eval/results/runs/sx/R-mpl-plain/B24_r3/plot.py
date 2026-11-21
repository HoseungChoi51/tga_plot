import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# Define paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B24_r3/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read the PE sheet
df_pe = pd.read_excel(DATA_FILE, sheet_name="PE")

# Extract columns
temp_c = df_pe["Temperature (°C)"]
weight = df_pe["Weight (%)"]
deriv_weight = df_pe["Deriv. Weight (%/°C)"]

# Convert Temperature from Celsius to Kelvin
temp_k = temp_c + 273.15

# Create figure with two subplots sharing x-axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot Weight (%) on primary y-axis
color1 = 'tab:blue'
ax1.set_xlabel('온도 (K)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
line1, = ax1.plot(temp_k, weight, color=color1, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', alpha=0.5)

# Create secondary y-axis for Derivative Weight
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('미분 무게 (%/K)', color=color2, fontsize=12)
line2, = ax2.plot(temp_k, deriv_weight, color=color2, label='미분 무게 (%/K)')
ax2.tick_params(axis='y', labelcolor=color2)

# Combine legends
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper right')

# Title
plt.title('PE 열중량 분석 (TGA) - 켈빈 단위', fontsize=14)

# Adjust layout
fig.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "pe_tga_kelvin.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
