import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# Extract downtime column
downtime_data = df["정지시간(분)"].dropna()

# Define log-spaced bin edges as requested
bins = [5, 10, 20, 50, 100, 200, 500, 1000]

# Create histogram with log-x axis
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(downtime_data, bins=bins, edgecolor='black', alpha=0.7, color='steelblue')

# Set x-axis to logarithmic scale
ax.set_xscale('log')

# Add labels and title
ax.set_xlabel("정지시간 (분)")
ax.set_ylabel("빈도 수")
ax.set_title("정지시간 분포 히스토그램 (로그 스케일)")

# Add grid for better readability
ax.grid(True, which="both", ls="--", linewidth=0.5)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "downtime_histogram_log.png")
plt.savefig(output_path, dpi=300)
plt.close()
