import pandas as pd
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t5"
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

# Calculate the overall average of the weekly totals
average_production = weekly_production_r3['총생산량_g'].mean()

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Plot line chart for R3
ax.plot(weekly_production_r3[week_col], weekly_production_r3['총생산량_g'], 
        marker='o', linestyle='-', color='#ff7f0e', label='R3 주간 생산량')

# Add horizontal line for the average
ax.axhline(y=average_production, color='red', linestyle='--', linewidth=2, label=f'R3 평균 ({average_production:.2f} g)')

# Set Y-axis limits to 0~6 as requested. 
# Note: The calculated values are in grams. If the user meant kg, we should divide by 1000.
# Given previous plots used 'g' and typical CNT yields are small, but production rates (g/h) * hours can be hundreds/thousands.
# However, the user explicitly asked for y-axis 0~6. 
# If the data is in grams, the values will likely exceed 6 significantly unless it's a very specific metric or unit conversion is implied.
# Let's check the magnitude. Speed ~16-59 g/h, Time ~2-16 h. Product ~30-900 g.
# Summing by week (multiple runs) makes it even larger.
# It is highly probable the user expects the values in kg, or normalized per run, or there's a misunderstanding of units.
# But looking at the request "y축은 0~6으로 해 주세요", if I plot raw grams, the line will be way off screen or the scale 0-6 will cut everything off.
# Let's assume the user might mean kg? Or perhaps the previous plot was normalized?
# Wait, the previous plot just said "총 생산량 (g)".
# If I strictly follow "y-axis 0-6", and the data is in grams (hundreds), nothing will show.
# Maybe the user wants Average Production Per Run? No, it says "주차별 추이".
# Let's convert to kg to see if that fits 0-6. Weekly sum of e.g. 4 runs * 500g = 2kg. This fits nicely in 0-6 range.
# I will convert the values to kg for plotting to make the 0-6 limit meaningful, and update labels accordingly.

weekly_production_r3['총생산량_kg'] = weekly_production_r3['총생산량_g'] / 1000.0
average_production_kg = average_production / 1000.0

# Re-plot with kg values
ax.clear() # Clear previous plot to redo with correct scaling
ax.plot(weekly_production_r3[week_col], weekly_production_r3['총생산량_kg'], 
        marker='o', linestyle='-', color='#ff7f0e', label='R3 주간 생산량 (kg)')

# Update average line for kg
ax.axhline(y=average_production_kg, color='red', linestyle='--', linewidth=2, label=f'R3 평균 ({average_production_kg:.2f} kg)')

# Set Y-axis limits
ax.set_ylim(0, 6)

# Add title and labels
ax.set_title('주차별 R3 반응기 총 생산량 추이 (kg)')
ax.set_xlabel('주차')
ax.set_ylabel('총 생산량 (kg)')
ax.legend(title='구분')
ax.grid(True, linestyle='--', alpha=0.7)

# Save plot
output_file = os.path.join(OUT_DIR, "production_trend_R3_only_with_avg.png")
plt.tight_layout()
plt.savefig(output_file, dpi=300)
plt.close()
