import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t2"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the data file
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# Robustly identify the sample column (contains 'TEM' values)
sample_col = None
for col in df.columns:
    if df[col].astype(str).str.contains('TEM').any():
        sample_col = col
        break

# Fallback logic if strict search fails
if sample_col is None:
    df.columns = df.columns.str.strip()
    candidates = ['A 시료', '시료', 'Sample']
    for c in candidates:
        if c in df.columns:
            sample_col = c
            break
if sample_col is None:
    sample_col = df.columns[0]

# Identify diameter column
diam_col = None
for col in df.columns:
    if '직경' in col or 'diameter' in col.lower():
        diam_col = col
        break
if diam_col is None:
    # Assume numeric column that isn't index or other categorical info
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        diam_col = num_cols[0]

# Calculate mean and standard deviation per sample
grouped = df.groupby(sample_col)[diam_col].agg(['mean', 'std']).reset_index()
grouped = grouped.sort_values(by=sample_col)

# Prepare data for plotting
labels = grouped[sample_col].values
means = grouped['mean'].values
stds = grouped['std'].values  # This will be used for error bars

# Create the bar plot with error bars
plt.figure(figsize=(10, 6))
bars = plt.bar(labels, means, yerr=stds, capsize=5, color='skyblue', edgecolor='black', alpha=0.7, ecolor='red')

# Add labels and title
plt.title('시료별 평균 직경 및 표준편차 (TEM Diameter)', fontsize=14)
plt.xlabel('시료 (Sample)', fontsize=12)
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
output_path = os.path.join(OUT_DIR, 'mean_diameter_by_sample_with_std.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
