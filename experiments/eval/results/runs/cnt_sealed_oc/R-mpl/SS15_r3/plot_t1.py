import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Configure font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify the correct column name for CNT yield by searching for '수율'
col_name = None
for col in df.columns:
    if 'CNT수율' in str(col):
        col_name = col
        break

if col_name is None:
    raise ValueError("Column containing 'CNT수율' not found.")

# Extract CNT yield data and ensure it is numeric
# The error suggests the column might contain non-numeric data (strings/NaNs mixed in a way that confuses mpl units)
# We force conversion to numeric, dropping errors/NaNs
yield_data = pd.to_numeric(df[col_name], errors='coerce').dropna()

# Create histogram
plt.figure(figsize=(10, 6))
n, bins, patches = plt.hist(yield_data.values, bins=30, edgecolor='black', color='steelblue')

# Add labels and title
plt.xlabel("CNT수율 (g/g-cat)", fontsize=12)
plt.ylabel("빈도 (Count)", fontsize=12)
plt.title("CNT수율 히스토그램 (30 bins)", fontsize=14)
plt.grid(axis='y', alpha=0.75)
plt.grid(axis='x', alpha=0.75)

# Save the plot
output_file = os.path.join(OUT_DIR, "cnt_yield_histogram.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
