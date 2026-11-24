import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
sheet_name = "런로그"

# Load data
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean column names to handle potential whitespace issues and identify the yield column
# The preview shows 'Q CNT수율 (g/g-cat)', but actual Excel headers might have spaces or different formatting.
# We search for a column containing 'CNT' and '수율' to be robust against minor header variations.
yield_col = None
for col in df.columns:
    if isinstance(col, str) and ('CNT' in col) and ('수율' in col):
        yield_col = col
        break

if yield_col is None:
    # Fallback: try exact match with stripped spaces just in case logic above failed due to encoding
    # But usually iterating and checking substrings is safer for Korean/English mixed headers
    raise ValueError("Could not find CNT yield column in headers")

week_col = '주차'

# Ensure columns are numeric
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')

# Drop rows with missing values in these columns for grouping purposes
df_clean = df.dropna(subset=[week_col, yield_col])

# Calculate weekly mean CNT yield per week (pooling all reactors)
weekly_mean = df_clean.groupby(week_col)[yield_col].mean().reset_index()

# Sort by week to ensure correct rolling calculation
weekly_mean = weekly_mean.sort_values(week_col).reset_index(drop=True)

# Calculate 4-week trailing rolling mean
# min_periods=1 ensures that we get a value even if less than 4 weeks have passed
weekly_mean['Rolling_Mean_4wk'] = weekly_mean[yield_col].rolling(window=4, min_periods=1).mean()

# Create the plot
plt.figure(figsize=(12, 7))

# Plot Weekly Mean
plt.plot(weekly_mean[week_col], weekly_mean[yield_col], marker='o', linestyle='-', label='주간 평균 수율', color='#1f77b4')

# Plot 4-week Trailing Rolling Mean
plt.plot(weekly_mean[week_col], weekly_mean['Rolling_Mean_4wk'], marker='s', linestyle='--', label='4주 이동평균', color='#ff7f0e')

# Formatting
plt.title('주간별 평균 CNT 수율 및 4주 이동평균', fontsize=16)
plt.xlabel('주차', fontsize=12)
plt.ylabel(f'CNT 수율 ({yield_col.split("(")[-1].strip(")")})', fontsize=12) # Try to extract unit from column name dynamically if possible, else fallback
# Fallback for ylabel if parsing fails or is ugly:
plt.ylabel('CNT 수율 (g/g-cat)', fontsize=12)

plt.xticks(weekly_mean[week_col]) 
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='best', fontsize=12)

# Save the figure
output_file = os.path.join(OUT_DIR, "weekly_yield_trend.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
