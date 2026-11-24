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

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Extract the column for residual metal (wt%)
col_name = None
for col in df.columns:
    if "잔류금속" in str(col):
        col_name = col
        break

if col_name is None:
    raise ValueError("Column '잔류금속' not found in data.")

# Convert to numeric and drop NaNs to ensure we have float values
data = pd.to_numeric(df[col_name], errors='coerce').dropna()

# Define bins and range
bin_width = 0.25
min_val = 1.75
max_val = 6.5
bins = np.arange(min_val, max_val + bin_width, bin_width)

# Plot histogram
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(data, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)

# Add title and labels
ax.set_title('CNT 런로그 잔류금속(wt%) 분포 히스토그램', fontsize=14)
ax.set_xlabel('잔류금속 (wt%)', fontsize=12)
ax.set_ylabel('빈도 수', fontsize=12)

# Set x-axis limits to ensure full range is shown nicely
ax.set_xlim(min_val - 0.2, max_val + 0.2)

# Add grid
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Save figure
output_file = os.path.join(OUT_DIR, "histogram_residual_metal.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
