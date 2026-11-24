import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configuration for Korean text support and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data from Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Find the column containing 'CNT수율' to handle potential whitespace or header variations
target_col = None
for col in df.columns:
    if "CNT수율" in str(col):
        target_col = col
        break

if target_col is None:
    raise ValueError("Column containing 'CNT수율' not found in the dataframe.")

# Extract the relevant column for histogram and ensure it is numeric
yields = pd.to_numeric(df[target_col], errors='coerce').dropna()

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(yields, bins=30, color='steelblue', edgecolor='black')

# Add titles and labels
ax.set_title("CNT 수율 분포 히스토그램", fontsize=14)
ax.set_xlabel(target_col, fontsize=12)
ax.set_ylabel("빈도 (Count)", fontsize=12)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "histogram_cnt_yield.png")
plt.savefig(output_filename, dpi=300)
plt.close(fig)
