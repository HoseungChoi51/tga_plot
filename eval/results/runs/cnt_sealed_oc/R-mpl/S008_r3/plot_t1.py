import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"

# The previous error 'dtype->object' during mean calculation suggests that the column
# contains non-numeric values (e.g., strings or mixed types).
# We need to read the sheet and ensure numeric columns are converted to float.

df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Strip whitespace from all column names
df_runs.columns = df_runs.columns.str.strip()

# Identify columns by searching for keywords in column names
week_col = None
yield_col = None

for col in df_runs.columns:
    col_str = str(col)
    if '주차' in col_str:
        week_col = col
    if 'CNT수율' in col_str:
        yield_col = col

if week_col is None or yield_col is None:
    raise ValueError(f"Could not find required columns. Week: {week_col}, Yield: {yield_col}")

# Convert yield column to numeric, forcing errors to NaN to handle any string artifacts
df_runs[yield_col] = pd.to_numeric(df_runs[yield_col], errors='coerce')

# Drop rows where yield is NaN just to be safe for the groupby mean, 
# though pandas groupby.mean usually skips NaNs automatically.
df_clean = df_runs.dropna(subset=[week_col, yield_col])

# Ensure week column is numeric for plotting order if it's stored as text/object
df_clean[week_col] = pd.to_numeric(df_clean[week_col], errors='coerce')
df_clean = df_clean.dropna(subset=[week_col])

# Group by Week and calculate mean Yield
weekly_avg = df_clean.groupby(week_col)[yield_col].mean().reset_index()

# Rename columns for easier handling
weekly_avg.columns = ['Week', 'Avg_Yield']

# Sort by Week
weekly_avg = weekly_avg.sort_values('Week')

# Create the plot
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(weekly_avg['Week'], weekly_avg['Avg_Yield'], marker='o', linestyle='-', color='#1f77b4', label='주차별 평균 수율')

# Add vertical dashed line at Week 14
ax.axvline(x=14, color='red', linestyle='--', linewidth=1.5)

# Add text annotation near the line
# Check if week 14 exists in our calculated averages to get the Y position
y_val_at_14 = weekly_avg.loc[weekly_avg['Week'] == 14, 'Avg_Yield'].values
if len(y_val_at_14) > 0:
    y_pos = y_val_at_14[0] + 0.5
else:
    # Fallback if week 14 is missing (unlikely given data preview), use overall max/median
    y_pos = weekly_avg['Avg_Yield'].max() * 0.8 

ax.text(14, y_pos, 'FC-2606 투입', color='red', ha='center', va='bottom', fontsize=12, weight='bold')

# Labels and Title
ax.set_xlabel('주차 (Week)', fontsize=12)
ax.set_ylabel('평균 CNT 수율 (g/g-cat)', fontsize=12)
ax.set_title('주차별 평균 CNT 수율 추이', fontsize=14, weight='bold')

# Grid and Legend
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='best')

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "weekly_yield_trend.png")
plt.savefig(output_filename, dpi=300)
plt.close()
