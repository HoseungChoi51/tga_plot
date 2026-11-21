import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the data file
file_path = "data/diameters.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# The column name in the preview was 'A 시료', but sometimes CSV headers might have extra spaces or different naming.
# Let's check the actual columns to be safe and identify the sample column.
# Based on the error, 'A 시료' was not found. It might be just '시료' or have a prefix issue.
# Looking at the preview: A 시료 [텍스트 6종...]. 
# Often in these datasets, the column header might simply be '시료' or the first column.
# Let's assume the first column is the sample identifier based on typical structure if exact match fails,
# but strictly following the prompt's hint that headers are read "as they are", it's possible there's a BOM or space.
# However, a more robust way is to find the column containing the TEM IDs (TEM-01 etc).

sample_col = None
for col in df.columns:
    # Check if this column contains the expected sample values
    if df[col].astype(str).str.contains('TEM').any():
        sample_col = col
        break

# If still not found, try stripping whitespace from column names and matching
if sample_col is None:
    df.columns = df.columns.str.strip()
    # Try common variations
    candidates = ['A 시료', '시료', 'Sample']
    for c in candidates:
        if c in df.columns:
            sample_col = c
            break
    
# Fallback to first column if logic above fails (risky but prevents crash)
if sample_col is None:
    sample_col = df.columns[0]

# Calculate mean diameter per sample
mean_diameter = df.groupby(sample_col)['직경(nm)'].mean().reset_index()

# Sort by sample name for consistent ordering
mean_diameter = mean_diameter.sort_values(by=sample_col)

# Create the bar plot
plt.figure(figsize=(10, 6))
bars = plt.bar(mean_diameter[sample_col], mean_diameter['직경(nm)'], color='skyblue', edgecolor='black')

# Add labels and title
plt.title('시료별 평균 직경 (TEM Diameter)', fontsize=14)
plt.xlabel('시료 (Sample)', fontsize=12)
plt.ylabel('평균 직경 (nm)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels on top of bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.2f}',
             ha='center', va='bottom', fontsize=9)

# Save the figure
output_path = os.path.join(OUT_DIR, 'mean_diameter_by_sample.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
