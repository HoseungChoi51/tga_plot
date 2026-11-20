import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the Excel file and specific sheets
file_path = "data/tga_batches.xlsx"
sheet1_name = "R3-260428-1"
sheet2_name = "R3-260810-2"

df1 = pd.read_excel(file_path, sheet_name=sheet1_name)
df2 = pd.read_excel(file_path, sheet_name=sheet2_name)

# Extract columns based on preview description
# A: 시간 (min), B: 온도 (°C), C: 중량 (%), D: 미분중량 (%/°C)
cols = ['시간 (min)', '온도 (°C)', '중량 (%)', '미분중량 (%/°C)']

# Use column indices to be safe against header variations, mapping 1->B(Temp), 2->C(Weight), 3->D(DTG)
temp_col_idx = 1
weight_col_idx = 2
dtg_col_idx = 3

# Prepare data arrays for plot 1
t1 = df1.iloc[:, temp_col_idx]
w1 = df1.iloc[:, weight_col_idx]
d1 = df1.iloc[:, dtg_col_idx]

# Prepare data arrays for plot 2
t2 = df2.iloc[:, temp_col_idx]
w2 = df2.iloc[:, weight_col_idx]
d2 = df2.iloc[:, dtg_col_idx]

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(12, 8))

# Define colors for batches
color_batch1 = 'blue'
color_batch2 = 'green'

# Plot TG curves (Solid lines) on left y-axis
ax1.plot(t1, w1, color=color_batch1, linestyle='-', linewidth=1.5, label=f'{sheet1_name} TG')
ax1.plot(t2, w2, color=color_batch2, linestyle='-', linewidth=1.5, label=f'{sheet2_name} TG')

ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color='black') # Keep label black or adjust if needed, but usually one color per axis is fine. 
# To match user request of distinct batch colors, we keep axis labels standard black, lines colored.
ax1.tick_params(axis='y', labelcolor='black')
ax1.grid(True, linestyle='--', alpha=0.5)

# Create a secondary y-axis for DTG curves (Dotted lines)
ax2 = ax1.twinx()

ax2.plot(t1, d1, color=color_batch1, linestyle=':', linewidth=1.5, label=f'{sheet1_name} DTG')
ax2.plot(t2, d2, color=color_batch2, linestyle=':', linewidth=1.5, label=f'{sheet2_name} DTG')

ax2.set_ylabel('미분중량 (%/°C)', color='black')
ax2.tick_params(axis='y', labelcolor='black')

# Add title
plt.title(f'TG/DTG Comparison - {sheet1_name} & {sheet2_name}')

# Add legend combining both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right', framealpha=0.9)

# Save the plot
output_filename = f"TGA_Comparison_{sheet1_name}_{sheet2_name}.png"
output_path = os.path.join(OUT_DIR, output_filename)
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
