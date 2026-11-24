import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configuration for Korean text support and output directory
plt.rcParams["font.family"] = "Noto Sans CJK KR"
OUT_DIR = "out/t3"
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

# Ensure the yield column is numeric
df[target_col] = pd.to_numeric(df[target_col], errors='coerce')

# Define shared bin edges: 1 g/g-cat wide from 12 to 36
bins = np.arange(12, 37, 1)

# Filter data for Period 1 (Weeks 1-13) and Period 2 (Weeks 14-26)
# Assuming '주차' column exists based on preview
week_col = None
for col in df.columns:
    if "주차" in str(col):
        week_col = col
        break

if week_col is None:
    raise ValueError("Column containing '주차' not found.")

df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

period1_yields = df.loc[(df[week_col] >= 1) & (df[week_col] <= 13), target_col].dropna()
period2_yields = df.loc[(df[week_col] >= 14) & (df[week_col] <= 26), target_col].dropna()

# Calculate medians
median_p1 = period1_yields.median()
median_p2 = period2_yields.median()

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(period1_yields, bins=bins, alpha=0.5, label='주차 1–13', color='steelblue', edgecolor='black')
ax.hist(period2_yields, bins=bins, alpha=0.5, label='주차 14–26', color='darkorange', edgecolor='black')

# Add vertical lines at medians
ax.axvline(median_p1, color='steelblue', linestyle='--', linewidth=2, label=f'주차 1–13 중앙값 ({median_p1:.2f})')
ax.axvline(median_p2, color='darkorange', linestyle='--', linewidth=2, label=f'주차 14–26 중앙값 ({median_p2:.2f})')

# Add titles and labels
ax.set_title("CNT 수율 분포 비교 (주차별)", fontsize=14)
ax.set_xlabel("CNT 수율 (g/g-cat)", fontsize=12)
ax.set_ylabel("빈도 (Count)", fontsize=12)
ax.legend()

# Adjust layout to prevent clipping
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "histogram_cnt_yield_periods_median.png")
plt.savefig(output_filename, dpi=300)
plt.close(fig)
