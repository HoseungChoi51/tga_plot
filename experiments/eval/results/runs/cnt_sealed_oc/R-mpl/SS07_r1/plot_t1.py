import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Extract the column for residual metal (wt%)
col_name = "잔류금속 (wt%)"
if col_name not in df.columns:
    # Try finding by partial match if exact header fails due to encoding/spaces issues
    matching_cols = [c for c in df.columns if "잔류금속" in str(c)]
    if matching_cols:
        col_name = matching_cols[0]
    else:
        raise ValueError("Column '잔류금속 (wt%)' not found.")

metal_data = df[col_name].dropna()

# Ensure the data is numeric. The error suggests that the data passed to hist might contain non-numeric types
# or that the bins were interpreted strangely. However, the previous code used linspace which produces floats.
# The error traceback points to matplotlib's category converter, which usually happens when plotting categorical data.
# This implies `metal_data` might still have string-like objects or NaNs that weren't handled properly before passing to hist?
# Or, more likely, the issue is simply that we need to ensure `metal_data` is a clean float array.

metal_data = pd.to_numeric(metal_data, errors='coerce').dropna()

# Define bins
# Range 1.75–6.5 with 0.25 wt% interval
# Calculate number of bins
num_bins = int((6.5 - 1.75) / 0.25) + 1
bin_edges = np.linspace(1.75, 6.5, num_bins)

# Plot histogram
fig, ax = plt.subplots(figsize=(10, 6))

# Use the cleaned numeric data
counts, bins, patches = ax.hist(metal_data.values, bins=bin_edges, color='skyblue', edgecolor='black', alpha=0.7)

ax.set_title("런로그 잔류금속(wt%) 분포 히스토그램", fontsize=14)
ax.set_xlabel("잔류금속 (wt%)", fontsize=12)
ax.set_ylabel("빈도 (횟수)", fontsize=12)

# Set x-axis limits to the requested range
ax.set_xlim(1.75, 6.5)

# Add grid
ax.grid(True, linestyle='--', alpha=0.6, axis='y')

# Save figure
output_filename = os.path.join(OUT_DIR, "histogram_residual_metal.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)

print(f"Plot saved to {output_filename}")
