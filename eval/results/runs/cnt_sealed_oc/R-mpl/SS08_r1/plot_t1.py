import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and ensure it exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Check if required columns exist (handling potential whitespace in headers)
cols = df.columns.tolist()
col_residual_metal = [c for c in cols if '잔류금속' in str(c)]
col_oxidation_temp = [c for c in cols if '산화개시온도' in str(c)]

if not col_residual_metal or not col_oxidation_temp:
    raise ValueError("Required columns '잔류금속 (wt%)' and '산화개시온도 (°C)' not found.")

residual_col = col_residual_metal[0]
temp_col = col_oxidation_temp[0]

# Clean data: convert to numeric and drop NaNs for plotting
df_plot = df[[residual_col, temp_col]].copy()
df_plot[residual_col] = pd.to_numeric(df_plot[residual_col], errors='coerce')
df_plot[temp_col] = pd.to_numeric(df_plot[temp_col], errors='coerce')
df_plot.dropna(inplace=True)

# Create the scatter plot
fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(df_plot[residual_col], df_plot[temp_col], alpha=0.6, edgecolors='k', s=50, color='steelblue')

# Add labels and title
ax.set_xlabel(residual_col, fontsize=12)
ax.set_ylabel(temp_col, fontsize=12)
ax.set_title('잔류금속 vs 산화개시온도 산점도', fontsize=14)

# Add grid for better readability
ax.grid(True, linestyle='--', alpha=0.5)

# Save the figure
output_filename = os.path.join(OUT_DIR, "scatter_residual_metal_vs_oxidation_temp.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
