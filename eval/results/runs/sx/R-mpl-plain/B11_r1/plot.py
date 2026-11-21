import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B11_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Read PET sheet
df = pd.read_excel(DATA_FILE, sheet_name='PET')

# Extract columns based on the preview info
# Column B: Temperature (°C), Column C: Weight (%), Column D: Deriv. Weight (%/°C)
temp = df['Temperature (°C)']
weight = df['Weight (%)']
deriv_weight = df['Deriv. Weight (%/°C)']

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot TGA curve (Weight %) on left y-axis
color1 = 'tab:blue'
ax1.set_xlabel('온도 (°C)', fontsize=12)
ax1.set_ylabel('무게 (%)', color=color1, fontsize=12)
line1 = ax1.plot(temp, weight, color=color1, label='무게 (%)')
ax1.tick_params(axis='y', labelcolor=color1)

# Create second y-axis for DTG curve (Deriv. Weight %/°C)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('미분 무게 (%/°C)', color=color2, fontsize=12)
line2 = ax2.plot(temp, deriv_weight, color=color2, linestyle='--', label='미분 무게 (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# Title
plt.title('PET 열분해', fontsize=14)

# Grid
ax1.grid(True, linestyle=':', alpha=0.7)

# Legend in lower left
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='lower left', fontsize=10)

# Format residual weight to 2 decimal places in the plot context if needed, 
# but usually this refers to axis ticks or just general precision. 
# The request says "잔류량은 소수 둘째 자리까지", which likely means formatting the Y-axis ticks or ensuring data display is precise.
# Let's format the y-ticks of the first axis (Weight %) to 2 decimal places.
from matplotlib.ticker import FuncFormatter
ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))

# Adjust layout to prevent label clipping
fig.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, 'PET_thermal_decomposition.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')

print(f"Plot saved to {output_path}")
