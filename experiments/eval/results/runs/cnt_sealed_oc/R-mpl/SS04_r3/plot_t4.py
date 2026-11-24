import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t4"
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

# Filter to keep only R3
df_r3 = df_clean[df_clean[reactor_col] == 'R3'].copy()

# Calculate total production per row (in grams)
df_r3['총생산량_g'] = df_r3[prod_speed_col] * df_r3[operating_time_col]

# Group by Week to get weekly production for R3
weekly_production_r3 = df_r3.groupby(week_col)['총생산량_g'].sum().reset_index()

# Sort by week
weekly_production_r3 = weekly_production_r3.sort_values(by=week_col)

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Plot line chart for R3 only
ax.plot(weekly_production_r3[week_col], weekly_production_r3['총생산량_g'], 
        marker='o', linestyle='-', color='#ff7f0e', label='R3') # Using orange for distinction

# Add title and labels
ax.set_title('주차별 R3 반응기 총 생산량 추이')
ax.set_xlabel('주차')
ax.set_ylabel('총 생산량 (g)')
ax.legend(title='반응기')
ax.grid(True, linestyle='--', alpha=0.7)

# Save plot
output_file = os.path.join(OUT_DIR, "production_trend_R3_only.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
