import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set output directory and ensure it exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Define grade order for consistent stacking (C at bottom, B middle, A top is common, 
# but user didn't specify. Let's use alphabetical or logical order. 
# Usually C->B->A or A->B->C. Let's stick to the unique values sorted or predefined.
grade_order = ['C', 'B', 'A']

# Create a cross-tabulation of Catalyst Lot vs Grade counts
ct_counts = pd.crosstab(df['촉매로트'], df['등급'])

# Ensure all grades are present, fill missing with 0
for g in grade_order:
    if g not in ct_counts.columns:
        ct_counts[g] = 0
        
# Reorder columns based on defined grade_order
ct_counts = ct_counts[grade_order]

# Calculate percentages for 100% stacked bar
row_sums = ct_counts.sum(axis=1)
ct_pct = ct_counts.div(row_sums, axis=0) * 100

# Sort lots chronologically
# Extract date from lot name (e.g., FC-2602 -> year 26, month 02)
def extract_sort_key(lot):
    # Format is usually FC-YYMM
    try:
        parts = str(lot).split('-')
        if len(parts) >= 2 and parts[1]:
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return float('inf') # Put unparsable ones at the end

# Get the original index list
original_lots = list(ct_pct.index)
# Create sort keys
sort_keys = [extract_sort_key(lot) for lot in original_lots]
# Get indices that would sort the keys
sorted_indices = np.argsort(sort_keys)
# Reorder the dataframe rows based on these sorted indices
sorted_lots = [original_lots[i] for i in sorted_indices]
ct_pct_sorted = ct_pct.loc[sorted_lots]

# Plotting
plt.figure(figsize=(12, 8))
colors = ['#ff9999', '#66b3ff', '#99ff99'] # C(red-ish), B(blue-ish), A(green-ish) - arbitrary but distinct

# Plot stacked bar chart
ax = ct_pct_sorted.plot(kind='bar', stacked=True, color=colors, rot=45, width=0.7)

# Formatting
plt.title('CNT 등급 분포별 촉매 로트별 비율 (100% Stacked Bar)', fontsize=16, pad=15)
plt.xlabel('촉매 로트', fontsize=12)
plt.ylabel('비율 (%)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.legend(title='등급', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add percentage labels inside bars if they are large enough
for p in ax.patches:
    height = p.get_height()
    if height > 5:  # Only label if slice is bigger than 5%
        ax.annotate(f'{height:.0f}%',
                    (p.get_x() + p.get_width() / 2., p.get_y() + height / 2.),
                    ha='center', va='center',
                    fontsize=9, color='black')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "grade_share_per_lot.png"), dpi=300, bbox_inches='tight')
plt.close()
