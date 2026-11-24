import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Create output directory if it doesn't exist
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name='정지이력')

# Extract the column of interest
downtime_col = '정지시간(분)'
if downtime_col in df.columns:
    downtime_values = df[downtime_col].dropna()
else:
    raise ValueError(f"Column '{downtime_col}' not found in the dataframe.")

# Define bin edges as requested
bin_edges = [5, 10, 20, 50, 100, 200, 500, 1000]

# Create the histogram
fig, ax = plt.subplots(figsize=(8, 6))

ax.hist(downtime_values, bins=bin_edges, edgecolor='black', color='steelblue')

# Set x-axis to log scale
ax.set_xscale('log')

# Labels and title
ax.set_xlabel('정지시간 (분)')
ax.set_ylabel('빈도')
ax.set_title('Downtime 정지시간 분포 히스토그램 (Log-X)')

# Add grid for better readability on log scale
ax.grid(True, which="both", ls="--", alpha=0.5)

# Adjust layout and save
plt.tight_layout()
output_path = os.path.join(OUT_DIR, "downtime_histogram_logx.png")
plt.savefig(output_path, dpi=300)
plt.close(fig)

print(f"Histogram saved to {output_path}")
