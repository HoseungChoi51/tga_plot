import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t3"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the data file
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# Robustly identify columns based on content or header names
# Sample column (contains TEM IDs) - needed for grouping if we want per-sample stats, 
# but user asked to change labels to 'Reactor / Catalyst Lot'.
# This implies we should group by Reactor and Catalyst Lot instead of just Sample.
# However, usually diameter varies by sample within a run. Let's assume the user wants
# mean/std of diameters grouped by [Reactor, Catalyst Lot].

reactor_col = None
catalyst_col = None
diam_col = None

for col in df.columns:
    col_str = str(col)
    if '반응기' in col_str or 'reactor' in col_str.lower():
        reactor_col = col
    elif '촉매로트' in col_str or 'lot' in col_str.lower() or 'catalyst' in col_str.lower():
        catalyst_col = col
    elif '직경' in col_str or 'diameter' in col_str.lower():
        diam_col = col

# Fallbacks if strict matching fails
if reactor_col is None:
    # Look for R1-R4 pattern
    for col in df.columns:
        if df[col].astype(str).str.contains('R[1-4]').any():
            reactor_col = col
            break
            
if catalyst_col is None:
    # Look for FC pattern
    for col in df.columns:
        if df[col].astype(str).str.contains('FC').any():
            catalyst_col = col
            break

if diam_col is None:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        diam_col = num_cols[0]

if not all([reactor_col, catalyst_col, diam_col]):
    raise ValueError("Could not identify required columns for Reactor, Catalyst Lot, or Diameter.")

# Create a combined label column
df['Label'] = df[reactor_col].astype(str) + ' / ' + df[catalyst_col].astype(str)

# Calculate mean and standard deviation per Label
grouped = df.groupby('Label')[diam_col].agg(['mean', 'std']).reset_index()
grouped = grouped.sort_values(by='Label')

# Prepare data for plotting
labels = grouped['Label'].values
means = grouped['mean'].values
stds = grouped['std'].values

# Create the bar plot with error bars
plt.figure(figsize=(12, 7)) # Wider figure for potentially more labels
bars = plt.bar(labels, means, yerr=stds, capsize=5, color='skyblue', edgecolor='black', alpha=0.7, ecolor='red')

# Add labels and title
plt.title('반응기/촉매로트별 평균 직경 및 표준편차', fontsize=14)
plt.xlabel('반응기 / 촉매로트', fontsize=12)
plt.ylabel('평균 직경 (nm)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels on top of bars (Mean ± Std)
for i, bar in enumerate(bars):
    height = bar.get_height()
    std = stds[i]
    # Position text above the error bar cap
    text_y = height + std
    plt.text(bar.get_x() + bar.get_width()/2., text_y,
             f'{height:.2f}±{std:.2f}',
             ha='center', va='bottom', fontsize=9)

# Save the figure
output_path = os.path.join(OUT_DIR, 'mean_diameter_by_reactor_lot.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
