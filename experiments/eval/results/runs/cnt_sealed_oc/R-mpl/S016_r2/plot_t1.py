import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define paths and output directory
input_file = "data/tga_batches.xlsx"
out_dir = "out"
os.makedirs(out_dir, exist_ok=True)

# Sheets to plot
sheets = ["R4-260407-1", "R4-260721-1"]

# Read data for each sheet
fig, ax = plt.subplots(figsize=(8, 6))

colors = ["blue", "red"]
labels = []

for i, sheet_name in enumerate(sheets):
    # Read the specific sheet
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    
    # Extract columns: '온도 (°C)' and '중량 (%)'
    # Assuming headers are exactly as in preview
    temp_col = "온도 (°C)"
    weight_col = "중량 (%)"
    
    x = df[temp_col]
    y = df[weight_col]
    
    ax.plot(x, y, color=colors[i], label=sheet_name, linewidth=1.5)

# Configure axes
ax.set_xlim(30, 900)
ax.set_ylim(0, 105)

ax.set_xlabel("온도 (°C)")
ax.set_ylabel("중량 (%)")
ax.set_title("TGA 곡선 비교: R4 배치들")

# Add legend
ax.legend()

# Grid
ax.grid(True, linestyle="--", alpha=0.7)

# Save figure
output_path = os.path.join(out_dir, "tga_R4_overlay.png")
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()
