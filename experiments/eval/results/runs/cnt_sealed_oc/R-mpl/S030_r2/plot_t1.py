import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and create if not exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean column names to handle potential whitespace or hidden characters
df.columns = df.columns.str.strip()

# Find the actual column name for Grade. 
# The preview showed '등급 (A/B/C)', but sometimes Excel headers have extra spaces or different parentheses types.
grade_col = None
for col in df.columns:
    if '등급' in str(col):
        grade_col = col
        break

if grade_col is None:
    raise ValueError("Could not find a column containing '등급'")

metal_col = None
for col in df.columns:
    if '잔류금속' in str(col):
        metal_col = col
        break
        
raman_col = None
for col in df.columns:
    if 'IG/ID' in str(col) or 'Ig/Id' in str(col) or 'IG/ID'.lower() in str(col).lower():
        raman_col = col
        break

# Filter for Grade C runs only
# Ensure we compare with stripped string just in case values also have spaces
df_c = df[df[grade_col].astype(str).str.strip() == 'C'].copy()

# Define conditions based on user request:
# 1. Residual Metal > 5.0 wt%
cond_metal_high = df_c[metal_col] > 5.0
# 2. IG/ID < 2.2
cond_raman_low = df_c[raman_col] < 2.2

# Categorize the failures
# '둘 다' (Both): High Metal AND Low Raman
both_mask = cond_metal_high & cond_raman_low
# '잔류금속 > 5.0 wt%만' (Metal only): High Metal AND NOT Low Raman
metal_only_mask = cond_metal_high & ~cond_raman_low
# 'IG/ID < 2.2만' (Raman only): NOT High Metal AND Low Raman
raman_only_mask = ~cond_metal_high & cond_raman_low

# Calculate counts
count_both = both_mask.sum()
count_metal_only = metal_only_mask.sum()
count_raman_only = raman_only_mask.sum()

labels = [
    '잔류금속 > 5.0 wt%만', 
    'IG/ID < 2.2만', 
    '둘 다'
]
counts = [
    count_metal_only, 
    count_raman_only, 
    count_both
]

# Filter out zero counts to keep pie chart clean
non_zero_indices = [i for i, c in enumerate(counts) if c > 0]

if non_zero_indices:
    labels_plot = [labels[i] for i in non_zero_indices]
    counts_plot = [counts[i] for i in non_zero_indices]
else:
    # Fallback if no data fits criteria
    labels_plot = ['No Failures Found']
    counts_plot = [1]

# Create Pie Chart
fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(
    counts_plot, 
    labels=labels_plot, 
    autopct='%1.1f%%', 
    startangle=90,
    colors=['#ff9999', '#66b3ff', '#99ff99'][:len(labels_plot)] # Adjust color list length
)

# Adjust text properties for readability
ax.set_title('등급 C 판정 런들의 불합격 사유 비율 분포', fontsize=14, pad=20)

# Save figure
output_filename = os.path.join(OUT_DIR, "grade_c_failure_reasons_pie.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close(fig)
