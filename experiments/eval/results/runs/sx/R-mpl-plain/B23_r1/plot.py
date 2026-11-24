import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'

# File paths
DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/cnt_batches.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-plain/B23_r1/out"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Define sheets and corresponding colors
sheets_colors = {
    "Raw": "black",
    "Acid-washed": "blue",
    "Annealed": "red"
}

fig, ax1 = plt.subplots(figsize=(10, 6))

for sheet_name, color in sheets_colors.items():
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    
    # Extract columns based on the preview structure
    temp_col = "Temperature (°C)"
    weight_col = "Weight (%)"
    deriv_weight_col = "Deriv. Weight (%/°C)"
    
    # Plot Weight (%) on primary axis (left)
    line1, = ax1.plot(df[temp_col], df[weight_col], label=f"{sheet_name} - Weight (%)", color=color, linestyle='-')
    
    # Create secondary y-axis for Derivative Weight
    ax2 = ax1.twinx()
    line2, = ax2.plot(df[temp_col], df[deriv_weight_col], label=f"{sheet_name} - Deriv. Weight (%/°C)", color=color, linestyle='--', alpha=0.7)

# Labels and Titles
ax1.set_xlabel("Temperature (°C)")
ax1.set_ylabel("Weight (%)")
ax2.set_ylabel("Derivative Weight (%/°C)")
ax1.set_title("TGA Curves: Raw, Acid-washed, and Annealed Samples")

# Combine legends from both axes
lines_labels = ax1.get_legend_handles_labels()
lines_labels2 = ax2.get_legend_handles_labels()
all_lines = lines_labels[0] + lines_labels2[0]
all_labels = lines_labels[1] + lines_labels2[1]

ax1.legend(all_lines, all_labels, loc='center right', bbox_to_anchor=(1.15, 0.5), fontsize=8)

# Grid
ax1.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "tga_combined.png")
plt.savefig(output_path, dpi=300)
plt.close()
