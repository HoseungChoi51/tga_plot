import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set Korean font
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = "/home/chs/Work/tga_plot/tests/inputs/korean_excel.csv"
OUT_DIR = "/home/chs/Work/tga_plot/eval/results/runs/sx/R-mpl-brief/14_r3/out"

os.makedirs(OUT_DIR, exist_ok=True)

# Read data with encoding fallback
try:
    df = pd.read_csv(DATA_FILE, encoding='utf-8')
except UnicodeDecodeError:
    try:
        df = pd.read_csv(DATA_FILE, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_FILE, encoding='latin1')

# Extract columns based on preview info
time_col = "시간(분)"
temp_col = "온도(°C)"
weight_col = "무게(%)"
dtg_col = "미분무게(%/°C)"

x_data = df[temp_col].values
y1_data = df[weight_col].values
y2_data = df[dtg_col].values * -1  # Invert DTG so peaks point up

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(8, 6))

# Plot weight (left y-axis)
color1 = '#1f4e9c'
ax1.set_xlabel('온도(°C)', fontsize=12)
ax1.set_ylabel('무게(%)', color=color1, fontsize=12)
line1, = ax1.plot(x_data, y1_data, color=color1, label='무게(%)')
ax1.tick_params(axis='y', labelcolor=color1)

# Create secondary axis for DTG
ax2 = ax1.twinx()
color2 = '#c0392b'
ax2.set_ylabel('미분무게(%/°C)', color=color2, fontsize=12)
line2, = ax2.plot(x_data, y2_data, color=color2, label='미분무게(%/°C)')
ax2.tick_params(axis='y', labelcolor=color2)

# Title from sheet name (or file name since it's a single-sheet CSV effectively)
sheet_name = "korean_excel"
plt.title(sheet_name, fontsize=14)

# Find Residue at ~800°C
target_temp_residue = 800
idx_residue = np.argmin(np.abs(x_data - target_temp_residue))
residue_weight = y1_data[idx_residue]
residue_temp = x_data[idx_residue]

# Add residue marker and label
ax1.plot(residue_temp, residue_weight, 'o', color=color1, markersize=6)
ax1.annotate(f'Residue {residue_weight:.1f}%', 
             xy=(residue_temp, residue_weight),
             xytext=(residue_temp + 50, residue_weight + 10),
             arrowprops=dict(facecolor='black', arrowstyle='->'),
             fontsize=10, color=color1)

# Find Peak temperature > 150°C in inverted DTG
mask_peak = x_data > 150
if np.any(mask_peak):
    y2_masked = y2_data[mask_peak]
    x_masked = x_data[mask_peak]
    
    # Find the highest peak (max value of inverted DTG)
    idx_max_dtg = np.argmax(y2_masked)
    peak_temp = x_masked[idx_max_dtg]
    peak_val = y2_masked[idx_max_dtg]
    
    # Plot marker on the original DTG curve location (which is now positive due to inversion)
    # We plot on ax2 because that's where the inverted DTG lives visually relative to its own scale
    # But wait, we plotted y2_data * -1 on ax2. So the peak is at positive values on ax2.
    ax2.plot(peak_temp, peak_val, 'v', color=color2, markersize=6)
    ax2.annotate(f'{peak_temp:.0f} °C', 
                 xy=(peak_temp, peak_val),
                 xytext=(peak_temp - 100, peak_val + 0.2), # Adjust text position
                 arrowprops=dict(facecolor='black', arrowstyle='->'),
                 fontsize=10, color=color2)

# Legend
lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(0.1, 0.5))

plt.tight_layout()

# Save as PNG and PDF
base_filename = "korean_excel"
png_path = os.path.join(OUT_DIR, f"{base_filename}.png")
pdf_path = os.path.join(OUT_DIR, f"{base_filename}.pdf")

plt.savefig(png_path, dpi=300, format='png')
plt.savefig(pdf_path, format='pdf')

plt.close()
