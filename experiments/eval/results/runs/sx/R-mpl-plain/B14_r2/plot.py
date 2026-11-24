import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B14_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read PVC sheet
df_pvc = pd.read_excel(DATA_FILE, sheet_name="PVC")

# Extract columns
temp = df_pvc["Temperature (°C)"]
weight = df_pvc["Weight (%)"]
deriv_weight = df_pvc["Deriv. Weight (%/°C)"]

# Create figure with specified size and font size
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot TGA curve on primary axis
ax1.plot(temp, weight, color='blue', label='TGA (Weight %)', linewidth=2)
ax1.set_xlabel('Temperature (°C)', fontsize=16)
ax1.set_ylabel('Weight (%)', color='blue', fontsize=16)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xlim([30, 900])
ax1.set_ylim([0, 105])

# Create secondary axis for DTG
ax2 = ax1.twinx()
ax2.plot(temp, deriv_weight, color='red', label='DTG (Deriv. Weight %/°C)', linewidth=2)
ax2.set_ylabel('Deriv. Weight (%/°C)', color='red', fontsize=16)
ax2.tick_params(axis='y', labelcolor='red')

# Title
plt.title('PVC TGA/DTG Analysis', fontsize=18)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=14)

# Grid
ax1.grid(True, linestyle='--', alpha=0.7)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "pvc_tga.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
