import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data file
# The file is a CSV with semicolons and decimal commas based on general context, 
# but the preview doesn't explicitly state delimiter issues for this specific file.
# However, standard pandas read_csv might need adjustment if it's not comma-separated.
# Let's try default first, or infer from typical export issues. 
# Given the prompt mentions "one CSV export uses semicolons and decimal commas", 
# we should check if 'diameters.csv' fits that description. 
# Without explicit confirmation, safe bet is to try default, then fallback.
# Actually, looking at the header names like '직경(nm)', it's likely standard UTF-8 CSV.
# But to be robust against the "decimal comma" warning in instructions:
try:
    df = pd.read_csv("data/diameters.csv")
except UnicodeDecodeError:
    df = pd.read_csv("data/diameters.csv", encoding='cp949')
except Exception:
    # Fallback for semicolon delimiter and decimal comma if necessary
    df = pd.read_csv("data/diameters.csv", sep=';', decimal=',', encoding='utf-8')

# Ensure the diameter column is numeric
col_name = 'D 직경(nm)'
if col_name not in df.columns:
    # Try to find the column containing '직경'
    candidate_cols = [c for c in df.columns if '직경' in str(c)]
    if candidate_cols:
        col_name = candidate_cols[0]
    
df['diameter_nm'] = pd.to_numeric(df[col_name], errors='coerce')

# Drop rows where diameter could not be parsed (if any)
df_clean = df.dropna(subset=['diameter_nm'])

# Extract all diameters into a single array
all_diameters = df_clean['diameter_nm'].values

# Calculate mean and median
mean_val = np.mean(all_diameters)
median_val = np.median(all_diameters)

# Define bins: 4 to 28 nm with width 0.5 nm
bins = np.arange(4, 28 + 0.5, 0.5)

# Plot histogram
plt.figure(figsize=(10, 6))
counts, bin_edges, patches = plt.hist(all_diameters, bins=bins, edgecolor='black', alpha=0.7, color='skyblue', label='TEM Diameter Distribution')

# Add vertical lines for mean and median
plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f} nm')
plt.axvline(median_val, color='green', linestyle='-.', linewidth=2, label=f'Median: {median_val:.2f} nm')

# Formatting
plt.title('TEM Diameter Histogram (All Samples Combined)', fontsize=14)
plt.xlabel('Diameter (nm)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.legend(loc='best')
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Save figure
output_path = os.path.join(OUT_DIR, 'tem_diameter_histogram.png')
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()
