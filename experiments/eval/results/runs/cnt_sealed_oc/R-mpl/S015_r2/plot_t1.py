import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to handle potential whitespace or hidden characters
df.columns = df.columns.str.strip()

# Identify the correct column name for operating time robustly
target_col = None
for col in df.columns:
    if '가동시간' in str(col):
        target_col = col
        break

if target_col is None:
    raise ValueError("Could not find '가동시간' column in the dataframe.")

# Extract the relevant column and force it to numeric type
# This fixes the TypeError caused by mixed types (strings/floats) in the data
operating_time = pd.to_numeric(df[target_col], errors='coerce').dropna()

# Define histogram parameters based on user request
# 1-hour intervals from 2 to 17 h range.
# bins: [2,3,4,...,17,18] -> creates bars covering 2-18
bins = np.arange(2, 18 + 1, 1) 

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot histogram
counts, bin_edges, patches = ax.hist(operating_time, bins=bins, edgecolor='black', color='steelblue', alpha=0.7)

# Add title and labels
ax.set_title('가동시간 분포 히스토그램', fontsize=14, pad=15)
ax.set_xlabel('가동시간 (h)', fontsize=12)
ax.set_ylabel('빈도 수 (Count)', fontsize=12)

# Configure x-axis ticks to show integer boundaries clearly
ax.set_xticks(np.arange(2, 19, 1))

# Add grid for better readability
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Annotate counts on top of each bar
for count, rect in zip(counts, patches):
    height = rect.get_height()
    if height > 0:
        ax.annotate(f'{int(height)}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=9)

# Save the figure
output_filename = os.path.join(OUT_DIR, "operating_time_histogram.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
