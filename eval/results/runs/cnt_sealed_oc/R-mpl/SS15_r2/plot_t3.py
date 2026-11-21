import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and ensure it exists
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Robustly find the CNT yield column
yield_col = None
for col in df.columns:
    if isinstance(col, str) and 'CNT' in col and '수율' in col:
        yield_col = col
        break

if yield_col is None:
    for col in df.columns:
        if isinstance(col, str) and '수율' in col:
            yield_col = col
            break

# Convert to numeric, dropping non-numeric/NaN
df['CNT_Yield'] = pd.to_numeric(df[yield_col], errors='coerce')

# Find the week column and convert to numeric to avoid string comparison issues
week_col = None
for col in df.columns:
    if isinstance(col, str) and ('주차' in col or 'Week' in col):
        week_col = col
        break

if week_col is None:
    # Fallback based on preview description (Column C is 주차)
    # Index A=0, B=1, C=2. So index 2.
    week_col = df.columns[2]

# Ensure the week column is numeric
df['WeekNum'] = pd.to_numeric(df[week_col], errors='coerce')

# Define bins: 1 g/g-cat wide from 12 to 36
bin_edges = np.arange(12, 37, 1)

# Filter periods using numeric week column
period1_mask = (df['WeekNum'] >= 1) & (df['WeekNum'] <= 13)
period2_mask = (df['WeekNum'] >= 14) & (df['WeekNum'] <= 26)

data_period1 = df.loc[period1_mask, 'CNT_Yield'].dropna()
data_period2 = df.loc[period2_mask, 'CNT_Yield'].dropna()

# Calculate medians
median1 = data_period1.median() if not data_period1.empty else 0
median2 = data_period2.median() if not data_period2.empty else 0

# Create histogram
plt.figure(figsize=(10, 6))
plt.hist(data_period1, bins=bin_edges, alpha=0.5, label=f'주차 1–13 (중앙값: {median1:.2f})', color='skyblue', edgecolor='black')
plt.hist(data_period2, bins=bin_edges, alpha=0.5, label=f'주차 14–26 (중앙값: {median2:.2f})', color='salmon', edgecolor='black')

# Add vertical lines at medians
plt.axvline(median1, color='darkblue', linestyle='--', linewidth=2, label=f'주차 1–13 중앙값 ({median1:.2f})')
plt.axvline(median2, color='darkred', linestyle='--', linewidth=2, label=f'주차 14–26 중앙값 ({median2:.2f})')

# Add labels and title
plt.title('CNT 수율 분포 비교 (주차 1–13 vs 14–26)', fontsize=14)
plt.xlabel('CNT 수율 (g/g-cat)', fontsize=12)
plt.ylabel('빈도 (Frequency)', fontsize=12)
plt.legend()

# Save the plot
output_file = os.path.join(OUT_DIR, "cnt_yield_histogram_periods_median.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
