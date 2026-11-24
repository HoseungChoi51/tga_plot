import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Setup
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# File paths and sheets
file_path = "data/tga_batches.xlsx"
sheets_to_read = ['R1-260326-1', 'R1-260716-1']

fig, ax = plt.subplots(figsize=(10, 7))

for sheet_name in sheets_to_read:
    # Read data for the specific sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Identify columns (based on preview: A=Time, B=Temp, C=Weight%, D=DW%)
    # We need Temperature (B) and Weight % (C)
    temp_col = df.columns[1]
    weight_col = df.columns[2]
    
    t = df[temp_col].values
    w = df[weight_col].values
    
    # Calculate mass change between 200 and 450 °C
    # Find indices closest to 200 and 450
    idx_200 = np.argmin(np.abs(t - 200))
    idx_450 = np.argmin(np.abs(t - 450))
    
    w_200 = w[idx_200]
    w_450 = w[idx_450]
    delta_w = w_200 - w_450
    
    # Create label with calculated value
    label = f"{sheet_name}\nΔW(200-450°C) = {delta_w:.2f} wt%"
    
    # Plot TG curve
    ax.plot(t, w, label=label, linewidth=2)

# Formatting
ax.set_xlabel("온도 (°C)")
ax.set_ylabel("중량 (%)")
ax.set_title("R1 배치 TG 곡선 비교 (200–450 °C 질량 변화 포함)")
ax.legend(loc="upper right", framealpha=0.9)
ax.grid(True, linestyle='--', alpha=0.6)

# Save plot
output_file = os.path.join(OUT_DIR, "tg_comparison_R1_delta_mass.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
