import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Output directory
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns
col_metal = "잔류금속 (wt%)"
if col_metal not in df.columns:
    matching_cols = [c for c in df.columns if "잔류금속" in str(c)]
    if matching_cols:
        col_metal = matching_cols[0]
    else:
        raise ValueError("Column '잔류금속 (wt%)' not found.")

col_reactor = "반응기"
if col_reactor not in df.columns:
    matching_cols = [c for c in df.columns if "반응기" in str(c)]
    if matching_cols:
        col_reactor = matching_cols[0]
    else:
        raise ValueError("Column '반응기' not found.")

# Clean data: ensure numeric type for metal content and handle missing values
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')
df_valid = df.dropna(subset=[col_metal])

# Split data into R4 and Others (R1-R3)
r4_data = df_valid[df_valid[col_reactor] == 'R4'][col_metal].values
other_data = df_valid[df_valid[col_reactor].isin(['R1', 'R2', 'R3'])][col_metal].values

# Define bins
# Range 1.75–6.5 with 0.25 wt% interval
num_bins = int((6.5 - 1.75) / 0.25) + 1
bin_edges = np.linspace(1.75, 6.5, num_bins)

# Plot histogram
fig, ax = plt.subplots(figsize=(10, 6))

# Plot R1-R3 first so R4 is on top, or vice versa depending on preference. 
# Using transparency allows seeing overlaps.
# density=True changes y-axis to probability density
ax.hist(other_data, bins=bin_edges, color='steelblue', edgecolor='black', alpha=0.5, label='R1-R3 (나머지)', density=True)
ax.hist(r4_data, bins=bin_edges, color='crimson', edgecolor='black', alpha=0.5, label='R4', density=True)

# Add vertical line for specification limit at 5.0 wt%
ax.axvline(x=5.0, color='green', linestyle='--', linewidth=1.5, label='규격 상한 (5.0 wt%)')

ax.set_title("반응기별 잔류금속(wt%) 분포 히스토그램 (밀도)", fontsize=14)
ax.set_xlabel("잔류금속 (wt%)", fontsize=12)
ax.set_ylabel("밀도 (Density)", fontsize=12)

# Set x-axis limits to the requested range
ax.set_xlim(1.75, 6.5)

# Add legend
ax.legend(loc='upper right')

# Add grid
ax.grid(True, linestyle='--', alpha=0.6, axis='y')

# Save figure
output_filename = os.path.join(OUT_DIR, "histogram_residual_metal_split_density.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
