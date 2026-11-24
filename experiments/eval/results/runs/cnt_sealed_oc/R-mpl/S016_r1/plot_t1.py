import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# File path
file_path = "data/tga_batches.xlsx"

# Sheets to read
sheets_to_read = ['R4-260407-1', 'R4-260721-1']

# Colors for the plots
colors = ['#1f77b4', '#ff7f0e']

fig, ax = plt.subplots(figsize=(10, 8))

for sheet_name, color in zip(sheets_to_read, colors):
    # Read data
    # Assuming header is in row 0 based on preview description "A 시간... | B 온도..."
    # The preview shows column headers like 'A 시간 (min)', but pandas will likely just see them if we don't skip rows.
    # However, sometimes these exports have a unit row or similar. Let's try standard read first.
    # If the header is actually the first row containing text, use default.
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Identify columns based on content or position from preview
    # Preview says: A 시간, B 온도, C 중량, D 미분중량
    # So Column 0: Time, Column 1: Temp, Column 2: Weight, Column 3: dW/dT
    
    temp_col = df.columns[1]
    weight_col = df.columns[2]
    
    temp = df[temp_col].values
    weight = df[weight_col].values
    
    # Plot TG curve
    ax.plot(temp, weight, label=sheet_name, color=color, linewidth=2)

# Set axis limits as requested
ax.set_xlim(30, 900)
ax.set_ylim(0, 105)

# Labels and Title
ax.set_xlabel("온도 (°C)", fontsize=12)
ax.set_ylabel("중량 (%)", fontsize=12)
ax.set_title("TG 곡선 비교: R4 시트", fontsize=14)

# Legend
ax.legend(loc='best', fontsize=10)

# Grid
ax.grid(True, linestyle='--', alpha=0.7)

# Save plot
output_filename = os.path.join(OUT_DIR, "tga_R4_overlay.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
