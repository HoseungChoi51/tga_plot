import pandas as pd
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Identify column names robustly based on preview description
# V 등급 (A/B/C), E 반응기, C 주차
cols = df.columns.tolist()

grade_col = next((c for c in cols if '등급' in str(c)), None)
reactor_col = next((c for c in cols if '반응기' in str(c)), None)
week_col = next((c for c in cols if '주차' in str(c)), None)

if not all([grade_col, reactor_col, week_col]):
    raise ValueError("Could not find required columns: 등급, 반응기, 주차")

# Clean and prepare data
# Ensure grade is string and stripped for comparison
df[grade_col] = df[grade_col].astype(str).str.strip()

# Create pass flag: A or B are passing
df['합격'] = df[grade_col].isin(['A', 'B'])

# Ensure Week is numeric for sorting and plotting
df[week_col] = pd.to_numeric(df[week_col], errors='coerce')

# Drop rows where essential fields are missing
df_clean = df.dropna(subset=[grade_col, reactor_col, week_col])

# Group by Reactor and Week to calculate pass rate
grouped = df_clean.groupby([reactor_col, week_col]).agg(
    total_runs=('합격', 'count'),
    passed_runs=('합격', 'sum')
).reset_index()

# Calculate percentage
grouped['pass_rate'] = (grouped['passed_runs'] / grouped['total_runs']) * 100

# Rename columns for easier access in plot loop
grouped.rename(columns={reactor_col: 'Reactor', week_col: 'Week'}, inplace=True)

# Create the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Plot lines for each reactor
reactors = ['R1', 'R2', 'R3', 'R4']
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

for i, reactor in enumerate(reactors):
    subset = grouped[grouped['Reactor'] == reactor].sort_values('Week')
    if not subset.empty:
        ax.plot(subset['Week'], subset['pass_rate'], 
                marker='o', 
                linestyle='-', 
                label=f'{reactor}', 
                color=colors[i], 
                linewidth=2)

# Formatting the plot
ax.set_title('반응기별 주차별 합격률 추이', fontsize=16, pad=10)
ax.set_xlabel('주차', fontsize=12)
ax.set_ylabel('합격률 (%)', fontsize=12)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend(title='반응기', loc='best')

# Set x-axis ticks
if not grouped.empty:
    min_week = int(grouped['Week'].min())
    max_week = int(grouped['Week'].max())
    # Avoid huge number of ticks if range is large, but here it's ~26 weeks so every tick is fine
    step = 1
    if (max_week - min_week) > 50:
        step = 5
    
    ticks = range(min_week, max_week + 1, step)
    ax.set_xticks(ticks)
    ax.tick_params(axis='x', rotation=45)

# Adjust layout
plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "pass_rate_by_reactor_and_week.png")
plt.savefig(output_file, dpi=300)
plt.close()
