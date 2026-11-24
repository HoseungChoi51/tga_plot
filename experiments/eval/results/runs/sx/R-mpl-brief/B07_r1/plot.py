import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Configure Korean font
font_path = None
for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f or "noto-sans-cjk" in f.lower():
        font_path = f
        break
if font_path:
    font_manager.fontManager.addfont(font_path)
    prop = font_manager.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK KR', 'Malgun Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/eval/inputs_b/polymers.xlsx"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/B07_r1/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read the second sheet only
sheet_names = pd.ExcelFile(DATA_FILE).sheet_names
target_sheet = sheet_names[1]  # Second sheet (index 1)

df = pd.read_excel(DATA_FILE, sheet_name=target_sheet)

# Identify columns based on standard TGA structure from preview
# x = Temperature, y1 = Weight, y2 = Deriv. Weight
temp_col = [c for c in df.columns if 'Temperature' in str(c)][0]
weight_col = [c for c in df.columns if 'Weight (%)' in str(c)][0]
dtg_col = [c for c in df.columns if 'Deriv.' in str(c) or 'DTG' in str(c)][0]

x = df[temp_col].values
y1 = df[weight_col].values
y2 = df[dtg_col].values * -1  # Invert DTG so peaks point up

fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot Weight (left axis)
color1 = '#1f4e9c'
ax1.set_xlabel('Temperature (°C)', fontsize=12)
ax1.set_ylabel('Weight (%)', color=color1, fontsize=12)
line1, = ax1.plot(x, y1, color=color1, linewidth=1.5, label='Weight')
ax1.tick_params(axis='y', labelcolor=color1)

# Create right axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.set_ylabel('DTG (%/°C)', color=color2, fontsize=12)
line2, = ax2.plot(x, y2, color=color2, linewidth=1.5, linestyle='--', label='DTG')
ax2.tick_params(axis='y', labelcolor=color2)

# Title is the sheet name
ax1.set_title(target_sheet, fontsize=14, pad=10)

# Combine legends
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

# Function to find weight at specific temperature
def get_weight_at_temp(temp_target):
    idx = np.argmin(np.abs(x - temp_target))
    return x[idx], y1[idx]

# Mark and label weight at 300 °C
t_300, w_300 = get_weight_at_temp(300)
ax1.scatter(t_300, w_300, color=color1, zorder=5, s=50)
ax1.annotate(f'{w_300:.1f}%', xy=(t_300, w_300), xytext=(t_300+20, w_300+5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=10, color='black', ha='left', va='bottom')

# Mark and label weight at 600 °C
t_600, w_600 = get_weight_at_temp(600)
ax1.scatter(t_600, w_600, color=color1, zorder=5, s=50)
ax1.annotate(f'{w_600:.1f}%', xy=(t_600, w_600), xytext=(t_600-40, w_600+5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=10, color='black', ha='right', va='bottom')

# Adjust layout
fig.tight_layout()

# Save figure
out_file = os.path.join(OUT_DIR, f"{target_sheet}.png")
plt.savefig(out_file, dpi=300, bbox_inches='tight')
plt.close(fig)
