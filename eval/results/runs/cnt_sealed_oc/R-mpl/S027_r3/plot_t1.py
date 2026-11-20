import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/diameters.csv"
df = pd.read_csv(file_path)

# Get the diameter column (column D: 직경(nm))
col_name = df.columns[3]  # '직경(nm)'
diameters = df[col_name].dropna()

# Compute mean and median
mean_val = diameters.mean()
median_val = diameters.median()

# Create histogram
fig, ax = plt.subplots(figsize=(10, 6))

# Bins from 4 to 28 with width 0.5 nm
bins = np.arange(4, 28 + 0.5, 0.5)
ax.hist(diameters, bins=bins, edgecolor='black', alpha=0.7, color='steelblue')

# Add vertical lines for mean and median
ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'평균: {mean_val:.2f} nm')
ax.axvline(median_val, color='green', linestyle='-', linewidth=2, label=f'중앙값: {median_val:.2f} nm')

# Labels and title
ax.set_xlabel('직경 (nm)', fontsize=12)
ax.set_ylabel('빈도 (Count)', fontsize=12)
ax.set_title('TEM 직경 분포 히스토그램 (모든 시료 합산)', fontsize=14)
ax.legend(loc='upper right')

# Set x-axis limits
ax.set_xlim(4, 28)

plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "tem_diameter_histogram.png")
plt.savefig(output_file, dpi=300)
plt.close()
