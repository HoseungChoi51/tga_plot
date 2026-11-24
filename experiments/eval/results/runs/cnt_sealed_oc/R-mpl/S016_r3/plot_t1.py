import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False  # To display negative signs correctly if needed

# Load the specific sheets from the Excel file
file_path = "data/tga_batches.xlsx"
sheet_names = ['R4-260407-1', 'R4-260721-1']

# Read data into a dictionary of DataFrames
dfs = {}
for sheet in sheet_names:
    dfs[sheet] = pd.read_excel(file_path, sheet_name=sheet)

# Create the plot
fig, ax = plt.subplots(figsize=(10, 7))

# Define colors for distinction
colors = ['#1f77b4', '#ff7f0e']

for i, sheet in enumerate(sheet_names):
    df = dfs[sheet]
    # Columns are assumed to be at index 1 (Temperature °C) and 2 (Weight %) based on preview:
    # A 시간 (min), B 온도 (°C), C 중량 (%), D 미분중량 (%/°C)
    # Using iloc to select columns by position to avoid header encoding issues
    temp_col_idx = 1
    weight_col_idx = 2
    
    x_data = df.iloc[:, temp_col_idx]
    y_data = df.iloc[:, weight_col_idx]
    
    ax.plot(x_data, y_data, label=sheet, color=colors[i], linewidth=2)

# Set axis limits as requested
ax.set_xlim(30, 900)
ax.set_ylim(0, 105)

# Labels and Title
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("중량 (%)")
ax.set_title("TGA 곡선 비교: R4-260407-1 vs R4-260721-1")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)

# Save the figure
output_file = os.path.join(OUT_DIR, "tga_overlay_R4.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close(fig)
