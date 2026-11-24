import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B07_r2/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read only the second sheet ("PVC")
sheet_name = "PVC"
df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)

# Identify columns based on the preview info
x_col = "Temperature (°C)"
y1_col = "Weight (%)"
y2_col = "Deriv. Weight (%/°C)"

temp = df[x_col].values
weight = df[y1_col].values
dtg = df[y2_col].values

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (%) on left y-axis
color1 = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1, = ax1.plot(temp, weight, color=color1, label='Weight (%)')
ax1.tick_params(axis='y', labelcolor=color1)

# Create right y-axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
# Multiply DTG by -1 so peaks point up
line2, = ax2.plot(temp, dtg * -1, color=color2, label='DTG (%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# Title is sheet name
ax1.set_title(sheet_name, fontsize=14)

# Find weights at 300°C and 600°C
def find_nearest_weight(target_temp, temps, weights):
    idx = np.argmin(np.abs(temps - target_temp))
    return temps[idx], weights[idx]

t_300, w_300 = find_nearest_weight(300, temp, weight)
t_600, w_600 = find_nearest_weight(600, temp, weight)

# Mark points on the curve
ax1.scatter([t_300, t_600], [w_300, w_600], color='black', zorder=5)

# Add annotations
ax1.annotate(f'{w_300:.2f}%', xy=(t_300, w_300), xytext=(t_300 + 20, w_300 + 5),
             arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10)
ax1.annotate(f'{w_600:.2f}%', xy=(t_600, w_600), xytext=(t_600 + 20, w_600 + 5),
             arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10)

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.02, 0.5))

plt.tight_layout()

# Save figure
out_path = os.path.join(OUT_DIR, f"{sheet_name}_custom.png")
plt.savefig(out_path, dpi=300)
plt.close()
