import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the specific sheet from the Excel file
file_path = "data/tga_batches.xlsx"
sheet_name = "R3-260428-1"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# Extract columns based on preview description
# A: 시간 (min), B: 온도 (°C), C: 중량 (%), D: 미분중량 (%/°C)
# The headers in the dataframe will be the first row.
try:
    # Attempt to use standard header names if present, otherwise fallback to column indices or known names
    time_col = df.columns[0]
    temp_col = df.columns[1]
    weight_col = df.columns[2]
    dtg_col = df.columns[3]
except IndexError:
    raise ValueError("Data format does not match expected 4 columns.")

# Create figure and axis
fig, ax1 = plt.subplots(figsize=(10, 7))

# Plot TG curve (Weight % vs Temperature) on left y-axis
ax1.plot(df[temp_col], df[weight_col], color='blue', label='TG (중량 %)')
ax1.set_xlabel('온도 (°C)')
ax1.set_ylabel('중량 (%)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, linestyle='--', alpha=0.5)

# Create a secondary y-axis for DTG curve
ax2 = ax1.twinx()
ax2.plot(df[temp_col], df[dtg_col], color='red', linestyle=':', label='DTG (미분중량 %/°C)')
ax2.set_ylabel('미분중량 (%/°C)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Add title
plt.title(f'TG/DTG Curve - {sheet_name}')

# Add legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

# Save the plot
output_filename = f"{sheet_name}_TG.png"
output_path = os.path.join(OUT_DIR, output_filename)
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
