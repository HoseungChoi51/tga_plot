import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify columns
col_metal = None
col_reactor = None
for col in df.columns:
    if "잔류금속" in str(col):
        col_metal = col
    if "반응기" in str(col):
        col_reactor = col

if col_metal is None or col_reactor is None:
    raise ValueError("Required columns not found.")

# Clean and prepare data
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')
df = df.dropna(subset=[col_metal, col_reactor])

# Split data into R4 and others (R1-R3)
r4_data = df[df[col_reactor] == 'R4'][col_metal]
others_data = df[df[col_reactor].isin(['R1', 'R2', 'R3'])][col_metal]

# Define bins and range
bin_width = 0.25
min_val = 1.75
max_val = 6.5
bins = np.arange(min_val, max_val + bin_width, bin_width)

# Plot histogram with overlapping transparency
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(others_data, bins=bins, color='steelblue', edgecolor='black', alpha=0.5, label='R1-R3 (나머지)')
ax.hist(r4_data, bins=bins, color='darkorange', edgecolor='black', alpha=0.5, label='R4')

# Add title and labels
ax.set_title('CNT 런로그 잔류금속(wt%) 분포 히스토그램 (반응기별 비교)', fontsize=14)
ax.set_xlabel('잔류금속 (wt%)', fontsize=12)
ax.set_ylabel('빈도 수', fontsize=12)

# Set x-axis limits to ensure full range is shown nicely
ax.set_xlim(min_val - 0.2, max_val + 0.2)

# Add grid
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Add legend
ax.legend(loc='upper right')

# Save figure
output_file = os.path.join(OUT_DIR, "histogram_residual_metal_by_reactor.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
