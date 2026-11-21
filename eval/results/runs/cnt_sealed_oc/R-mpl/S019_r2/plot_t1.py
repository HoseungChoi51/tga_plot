import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False  # To display minus sign correctly

# File path
file_path = "data/tga_batches.xlsx"

# Read all sheets
xl = pd.ExcelFile(file_path)
sheet_names = xl.sheet_names

# Create a new figure
fig, ax = plt.subplots(figsize=(10, 6))

colors = plt.cm.tab10(np.linspace(0, 1, len(sheet_names)))

for i, sheet_name in enumerate(sheet_names):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Extract columns based on preview: B=Temperature, D=Derivative Weight
    temp_col = '온도 (°C)'
    dtg_col = '미분중량 (%/°C)'
    
    # Ensure numeric types
    df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
    df[dtg_col] = pd.to_numeric(df[dtg_col], errors='coerce')
    
    # Drop NaNs
    df_clean = df.dropna(subset=[temp_col, dtg_col])
    
    # Filter for 500-700 °C range
    mask = (df_clean[temp_col] >= 500) & (df_clean[temp_col] <= 700)
    df_filtered = df_clean[mask]
    
    if not df_filtered.empty:
        ax.plot(df_filtered[temp_col], df_filtered[dtg_col], label=sheet_name, color=colors[i], linewidth=1.5)

# Plot configuration
ax.set_xlabel("온도 (°C)", fontsize=12)
ax.set_ylabel("DTG (미분중량, %/°C)", fontsize=12)
ax.set_title("DTG 곡선 비교 (500–700 °C 구간)", fontsize=14)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(title="배치", bbox_to_anchor=(1.05, 1), loc='upper left')

# Tight layout to prevent label clipping
plt.tight_layout()

# Save the plot
output_file = os.path.join(OUT_DIR, "dtg_comparison_500_700.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"Plot saved to {output_file}")
