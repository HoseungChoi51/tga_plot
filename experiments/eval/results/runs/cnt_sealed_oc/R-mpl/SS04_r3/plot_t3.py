import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Define column names based on preview
prod_speed_col = '생산속도 (g/h)'
operating_time_col = '가동시간 (h)'
reactor_col = '반응기'
week_col = '주차'

# Check if columns exist, otherwise try common variations if needed
if prod_speed_col not in df.columns:
    matching_cols = [c for c in df.columns if '생산속도' in str(c)]
    if matching_cols:
        prod_speed_col = matching_cols[0]

if operating_time_col not in df.columns:
    matching_cols = [c for c in df.columns if '가동시간' in str(c)]
    if matching_cols:
        operating_time_col = matching_cols[0]

if reactor_col not in df.columns:
    matching_cols = [c for c in df.columns if '반응기' in str(c)]
    if matching_cols:
        reactor_col = matching_cols[0]

if week_col not in df.columns:
    matching_cols = [c for c in df.columns if '주차' in str(c)]
    if matching_cols:
        week_col = matching_cols[0]

# Convert relevant columns to numeric to handle any string representations or errors
df[prod_speed_col] = pd.to_numeric(df[prod_speed_col], errors='coerce')
df[operating_time_col] = pd.to_numeric(df[operating_time_col], errors='coerce')
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

# Drop rows where conversion failed for necessary columns
df_clean = df.dropna(subset=[prod_speed_col, operating_time_col, week_col, reactor_col])

# Calculate total production per row (in grams)
df_clean['총생산량_g'] = df_clean[prod_speed_col] * df_clean[operating_time_col]

# Group by Week and Reactor to get weekly production per reactor
weekly_production = df_clean.groupby([week_col, reactor_col])['총생산량_g'].sum().reset_index()

# Pivot the data so each reactor is a column, weeks are index
pivot_df = weekly_production.pivot(index=week_col, columns=reactor_col, values='총생산량_g')

# Sort reactors for consistent ordering (e.g., R1, R2, R3, R4)
sorted_reactors = sorted(pivot_df.columns.tolist())
pivot_df = pivot_df[sorted_reactors]

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

colors = plt.cm.tab10.colors
for i, reactor in enumerate(sorted_reactors):
    ax.plot(pivot_df.index, pivot_df[reactor], marker='o', linestyle='-', color=colors[i % len(colors)], label=reactor)

# Add title and labels
ax.set_title('주차별 반응기별 총 생산량 추이')
ax.set_xlabel('주차')
ax.set_ylabel('총 생산량 (g)')
ax.legend(title='반응기')
ax.grid(True, linestyle='--', alpha=0.7)

# Save plot
output_file = os.path.join(OUT_DIR, "production_trend_by_week_reactor.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
