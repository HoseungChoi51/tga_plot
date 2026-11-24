import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Load data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name="런로그")

# Ensure '주차' is numeric and sorted for correct rolling calculation
df_runs['주차'] = pd.to_numeric(df_runs['주차'], errors='coerce')

# Identify the yield column name dynamically to avoid KeyError due to whitespace or formatting issues
yield_col = None
for col in df_runs.columns:
    if 'CNT수율' in col:
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT Yield column in the data.")

# Drop rows with missing week or yield (using non-inplace method)
df_runs_clean = df_runs.dropna(subset=['주차', yield_col]).copy()
df_runs_clean['주차'] = df_runs_clean['주차'].astype(int)

# Group by week to get weekly mean CNT yield
weekly_mean_df = df_runs_clean.groupby('주차')[yield_col].mean().reset_index()
weekly_mean_df.columns = ['Week', 'Mean_Yield']

# Sort by week to ensure chronological order for rolling average
weekly_mean_df.sort_values(by='Week', inplace=True)

# Calculate 4-week trailing rolling mean
# Using min_periods=1 allows plotting from the first week, treating early weeks as averages of available data
weekly_mean_df['Rolling_4W_Mean'] = weekly_mean_df['Mean_Yield'].rolling(window=4, min_periods=1).mean()

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Plot Weekly Mean
ax.plot(weekly_mean_df['Week'], weekly_mean_df['Mean_Yield'], marker='o', linestyle='-', color='b', label='Weekly Mean CNT Yield')

# Plot 4-week Trailing Rolling Mean
ax.plot(weekly_mean_df['Week'], weekly_mean_df['Rolling_4W_Mean'], linestyle='--', color='r', linewidth=2, label='4-week Trailing Rolling Mean')

# Labels and Title
ax.set_xlabel('주차 (Week)', fontsize=12)
ax.set_ylabel('CNT수율 (g/g-cat)', fontsize=12)
ax.set_title('주별 평균 CNT 수율 및 4주 이동평균', fontsize=14)
ax.legend(loc='best')
ax.grid(True, linestyle=':', alpha=0.7)

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "weekly_yield_vs_rolling_mean.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
