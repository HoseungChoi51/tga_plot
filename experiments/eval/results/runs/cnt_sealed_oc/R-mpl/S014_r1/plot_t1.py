import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Read Run Log (Weekly Summary) for Production Volume
run_log_path = "data/run_log.xlsx"
df_weekly_summary = pd.read_excel(run_log_path, sheet_name='주간요약')

# Ensure '주차' is numeric and clean data
df_weekly_summary['주차'] = pd.to_numeric(df_weekly_summary['주차'], errors='coerce')
df_weekly_summary = df_weekly_summary.dropna(subset=['주차'])
df_weekly_summary['총생산량(kg)'] = pd.to_numeric(df_weekly_summary['총생산량(kg)'], errors='coerce')

# 2. Read Downtime Log to calculate Weekly Total Downtime in Hours
downtime_path = "data/downtime.xlsx"
df_downtime = pd.read_excel(downtime_path, sheet_name='정지이력')

# Parse dates
df_downtime['일자'] = pd.to_datetime(df_downtime['일자'])

# Determine the start date of Week 1 based on user request: March 2nd is Week 1 Monday
week_1_start = pd.Timestamp('2026-03-02')

# Function to map a date to its week number relative to week_1_start
def get_week_number(date):
    delta_days = (date - week_1_start).days
    if delta_days < 0:
        return None # Before week 1
    # Weeks are 7 days long. Week 1 covers day 0-6.
    week_num = int(delta_days // 7) + 1
    return week_num

df_downtime['주차'] = df_downtime['일자'].apply(get_week_number)

# Filter out rows where week number could not be determined or is outside expected range if needed
df_downtime_valid = df_downtime.dropna(subset=['주차']).copy()

# Convert downtime from minutes to hours
df_downtime_valid['정지시간(분)'] = pd.to_numeric(df_downtime_valid['정지시간(분)'], errors='coerce')
df_downtime_valid['정지시간(시간)'] = df_downtime_valid['정지시간(분)'] / 60.0

# Aggregate total downtime by week
df_downtime_weekly = df_downtime_valid.groupby('주차')['정지시간(시간)'].sum().reset_index()
df_downtime_weekly.columns = ['주차', '총정지시간(시간)']

# 3. Merge Dataframes
# We use an outer join to see if there are weeks with production but no recorded downtime, or vice versa.
# However, since the weekly summary comes from run logs which likely cover all active weeks, 
# merging on the weekly summary index is appropriate.
merged_df = pd.merge(df_weekly_summary[['주차', '총생산량(kg)']], 
                     df_downtime_weekly, 
                     on='주차', 
                     how='left')

# Fill NaN downtime with 0 (assuming if no downtime record exists for that week, it was 0 or not logged)
merged_df['총정지시간(시간)'] = merged_df['총정지시간(시간)'].fillna(0)

# Drop rows where production data might be missing (though unlikely given the source)
merged_df = merged_df.dropna(subset=['총생산량(kg)'])

# 4. Plot Scatter Chart
fig, ax = plt.subplots(figsize=(10, 7))

scatter = ax.scatter(
    merged_df['총정지시간(시간)'], 
    merged_df['총생산량(kg)'],
    s=100,
    c=merged_df['주차'],
    cmap='viridis',
    edgecolors='k',
    alpha=0.8
)

ax.set_xlabel('주차별 총 정지시간 (시간)', fontsize=12)
ax.set_ylabel('주차별 총생산량 (kg)', fontsize=12)
ax.set_title('주차별 총 정지시간과 총생산량의 관계 산점도', fontsize=14)

# Add colorbar for week reference
cbar = fig.colorbar(scatter, ax=ax)
cbar.set_label('주차', fontsize=10)

# Calculate correlation for context
corr = merged_df['총정지시간(시간)'].corr(merged_df['총생산량(kg)'])
ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))

ax.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()

output_file = os.path.join(OUT_DIR, "downtime_vs_production_scatter.png")
plt.savefig(output_file, dpi=300)
plt.close()
