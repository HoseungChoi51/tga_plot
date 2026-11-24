import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configure Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

file_path = "data/tga_batches.xlsx"

# Read all sheets from the Excel file
xl_file = pd.ExcelFile(file_path)
sheet_names = xl_file.sheet_names

fig, ax1 = plt.subplots(figsize=(10, 6))

colors = plt.cm.tab10(np.linspace(0, 1, len(sheet_names)))

for i, sheet in enumerate(sheet_names):
    df = pd.read_excel(file_path, sheet_name=sheet)
    
    # Identify columns based on the preview:
    # B 온도 (°C), D 미분중량 (%/°C)
    temp_col = 'B' if 'B' in df.columns else df.columns[1] # Fallback to index if header names are complex
    dtg_col = 'D' if 'D' in df.columns else df.columns[3]
    
    # Ensure numeric conversion just in case headers or units rows cause issues
    df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
    df[dtg_col] = pd.to_numeric(df[dtg_col], errors='coerce')
    
    # Drop NaNs resulting from coercion
    df = df.dropna(subset=[temp_col, dtg_col])
    
    # Filter for 500–700 °C range
    mask = (df[temp_col] >= 500) & (df[temp_col] <= 700)
    df_filtered = df[mask]
    
    # Plot DTG curve
    label = f"{sheet} (DTG)"
    ax1.plot(df_filtered[temp_col], df_filtered[dtg_col], 
             color=colors[i], 
             label=label, 
             linewidth=1.5)
    
    # Find peak position within the filtered range for annotation
    if not df_filtered.empty:
        max_dtg_idx = df_filtered[dtg_col].idxmax()
        peak_temp = df_filtered.loc[max_dtg_idx, temp_col]
        peak_val = df_filtered.loc[max_dtg_idx, dtg_col]
        
        # Annotate peak temperature on the plot
        ax1.annotate(f'{peak_temp:.1f}°C', 
                     xy=(peak_temp, peak_val), 
                     xytext=(5, 5), 
                     textcoords='offset points', 
                     fontsize=8, 
                     color=colors[i])

ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Derivative Weight (%/°C)')
ax1.set_title('DTG Curves Comparison (500-700°C Range)')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='upper right', fontsize=8)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "dtg_comparison_500_700.png")
plt.savefig(output_path, dpi=300)
plt.close()
