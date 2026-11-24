import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"
sheets_to_plot = ['R1-260326-1', 'R1-260716-1']

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = ['#1f77b4', '#ff7f0e']

for i, sheet_name in enumerate(sheets_to_plot):
    # Read data
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Assume columns are: 시간 (min), 온도 (°C), 중량 (%), 미분중량 (%/°C) based on preview
    # Using positional indexing or robust header matching if needed, but preview suggests standard structure
    temp_col = df.columns[1]  # B 온도 (°C)
    weight_col = df.columns[2] # C 중량 (%)
    
    x_data = df[temp_col]
    y_data = df[weight_col]
    
    # Calculate mass loss between 200 and 450 °C
    # Filter data for temperatures near 200 and 450 to get accurate values
    # We find the closest points to avoid interpolation issues if grid is fine enough
    
    mask_200 = (x_data >= 195) & (x_data <= 205)
    mask_450 = (x_data >= 445) & (x_data <= 455)
    
    if not mask_200.any() or not mask_450.any():
        # Fallback: interpolate or use closest single point
        w200 = y_data.iloc[(x_data - 200).abs().idxmin()]
        w450 = y_data.iloc[(x_data - 450).abs().idxmin()]
    else:
        # Average weights in these small windows for stability
        w200 = y_data[mask_200].mean()
        w450 = y_data[mask_450].mean()
        
    mass_loss = w200 - w450
    
    label_text = f"{sheet_name}\nΔW(200-450°C) = {mass_loss:.2f} wt%"
    
    # Plot TG curve (Weight %) on left axis
    ax1.plot(x_data, y_data, color=colors[i], linewidth=2, label=label_text)

ax1.set_xlabel("온도 (°C)")
ax1.set_ylabel("중량 (%)", color='#1f77b4')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.grid(True, linestyle='--', alpha=0.5)

# Add legend
legend = ax1.legend(loc='upper right', framealpha=0.9)

plt.title("TG 곡선 비교: R1-260326-1 vs R1-260716-1")
plt.tight_layout()

output_filename = os.path.join(OUT_DIR, "tg_comparison_R1_mass_loss.png")
plt.savefig(output_filename, dpi=300)
plt.close()
