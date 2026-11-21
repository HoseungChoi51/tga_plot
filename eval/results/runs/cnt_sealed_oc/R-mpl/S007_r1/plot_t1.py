import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the run log data from Excel
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Ensure '주차' column is numeric to avoid sorting issues (str vs int comparison)
# Some rows might have text or mixed types if the header row wasn't skipped correctly in previous steps,
# but read_excel usually handles this. We force conversion to be safe.
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')
df.dropna(subset=['주차'], inplace=True)
df['주차'] = df['주차'].astype(int)

# Calculate pass/fail status based on Grade (A or B is pass, C is fail)
# 1 for Pass, 0 for Fail
df['합격여부'] = df['등급'].apply(lambda x: 1 if x in ['A', 'B'] else 0)

# Group by Reactor and Week to calculate average pass rate
# We want the percentage of runs that were A or B for each reactor-week combination
grouped = df.groupby(['반응기', '주차']).agg(
    total_runs=('합격여부', 'count'),
    passed_runs=('합격여부', 'sum')
).reset_index()

grouped['합격률(%)'] = (grouped['passed_runs'] / grouped['total_runs']) * 100

# Pivot the data to have reactors as columns and weeks as index for easier plotting
pivot_df = grouped.pivot(index='주차', columns='반응기', values='합격률(%)')

# Plotting
plt.figure(figsize=(12, 8))

# Sort weeks numerically just in case (now that they are integers)
pivot_df.sort_index(inplace=True)

for reactor in pivot_df.columns:
    # Drop NaNs for plotting individual lines to prevent breaks if a week has no data for that reactor
    valid_data = pivot_df[reactor].dropna()
    plt.plot(valid_data.index, valid_data.values, marker='o', label=f'반응기 {reactor}')

# Add title and labels
plt.title('반응기별 주차별 합격률 추이', fontsize=16)
plt.xlabel('주차', fontsize=12)
plt.ylabel('합격률 (%)', fontsize=12)

# Set x-axis ticks to integer weeks present in the data
all_weeks = sorted(pivot_df.index.unique())
plt.xticks(ticks=all_weeks, labels=all_weeks)

# Add grid
plt.grid(True, linestyle='--', alpha=0.7)

# Add legend
plt.legend(loc='best', fontsize=10)

# Save figure
output_filename = os.path.join(OUT_DIR, "pass_rate_by_reactor_week.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close()
