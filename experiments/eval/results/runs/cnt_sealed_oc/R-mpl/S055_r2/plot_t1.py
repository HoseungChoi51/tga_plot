import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Define chronological order of catalyst lots based on the lot ID string (FC-YYYYMM)
# The prefix is 'FC-', followed by year and month. Sorting lexicographically works for this format.
unique_lots = df['촉매로트'].unique()
lots_sorted = sorted(unique_lots, key=lambda x: x.split('-')[1]) # Sort by the numeric part FC-XXXXXX

# Create a categorical column to enforce order in groupby/plotting
df['촉매로트'] = pd.Categorical(df['촉매로트'], categories=lots_sorted, ordered=True)

# Pivot table to get counts of each grade per catalyst lot
pivot_counts = df.pivot_table(index='촉매로트', columns='등급', values='런ID', aggfunc='count', fill_value=0)

# Reindex columns to ensure consistent color mapping and order (A, B, C)
grade_order = ['A', 'B', 'C']
for g in grade_order:
    if g not in pivot_counts.columns:
        pivot_counts[g] = 0
pivot_counts = pivot_counts[grade_order]

# Convert to percentages for 100% stacked bar
row_sums = pivot_counts.sum(axis=1)
# Avoid division by zero just in case
row_sums[row_sums == 0] = 1 
pivot_pct = pivot_counts.div(row_sums, axis=0) * 100

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#2ca02c', '#ff7f0e', '#d62728'] # Green for A, Orange for B, Red for C
bottom = np.zeros(len(pivot_pct.index))

x_labels = [str(lot) for lot in pivot_pct.index]

for i, grade in enumerate(grade_order):
    values = pivot_pct[grade].values
    ax.bar(x_labels, values, bottom=bottom, label=f'등급 {grade}', color=colors[i], edgecolor='white')
    
    # Add percentage text inside bars if segments are large enough
    centers = bottom + values / 2
    for k, val in enumerate(values):
        if val > 5: # Only show text if segment is > 5%
            ax.text(k, centers[k], f'{val:.1f}%', ha='center', va='center', color='white', fontsize=9, weight='bold')
            
    bottom += values

ax.set_ylabel('비중 (%)')
ax.set_xlabel('촉매 로트')
ax.set_title('촉매 로트별 등급 구성 비율 (100% Stacked Bar)')
ax.legend(title='등급', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
output_file = os.path.join(OUT_DIR, "grade_share_by_catalyst_lot.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
