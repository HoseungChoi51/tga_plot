import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Configure font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory and ensure it exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Clean column names: strip whitespace to handle potential invisible spaces or mismatches
df.columns = df.columns.str.strip()

# Identify columns by partial match to be robust against slight naming differences
humidity_col = None
metal_col = None
date_col = None

for col in df.columns:
    if '외기습도' in col:
        humidity_col = col
    if '잔류금속' in col:
        metal_col = col
    if '일자' in col:
        date_col = col

if humidity_col is None or metal_col is None or date_col is None:
    raise ValueError("Could not find required columns (Humidity, Metal, Date)")

# Process Date column
# The previous error indicated a literal string "yyyy-mm-dd" might exist in the data rows
# Convert to datetime, coercing errors to NaT
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# Drop rows where date conversion failed (includes the 'yyyy-mm-dd' row if present)
df = df.dropna(subset=[date_col])

# Extract month
df['월'] = df[date_col].dt.month

# Filter for months 3 to 8
df_filtered = df[df['월'].isin([3, 4, 5, 6, 7, 8])]

# Ensure numeric types for plotting
df_filtered[humidity_col] = pd.to_numeric(df_filtered[humidity_col], errors='coerce')
df_filtered[metal_col] = pd.to_numeric(df_filtered[metal_col], errors='coerce')

# Drop any remaining NaNs in plot columns just in case
df_filtered = df_filtered.dropna(subset=[humidity_col, metal_col])

# Create a scatter plot
fig, ax = plt.subplots(figsize=(10, 7))

# Define colors for each month (3=March ... 8=August)
months = [3, 4, 5, 6, 7, 8]
colors = ['#ff9999', '#ffff99', '#99ff99', '#99ffff', '#9999ff', '#ff99ff']
month_labels = ['3월', '4월', '5월', '6월', '7월', '8월']

for m, c, label in zip(months, colors, month_labels):
    subset = df_filtered[df_filtered['월'] == m]
    if not subset.empty:
        ax.scatter(subset[humidity_col], subset[metal_col], 
                   color=c, alpha=0.6, edgecolors='k', linewidth=0.5, label=label)

# Set labels and title using the cleaned/identified column names
ax.set_xlabel(humidity_col)
ax.set_ylabel(metal_col)
ax.set_title('외기습도 vs 잔류금속 산점도 (월별 색상 구분)')
ax.legend(title='월', loc='best')
ax.grid(True, linestyle='--', alpha=0.5)

# Save the figure
output_filename = os.path.join(OUT_DIR, "scatter_humidity_residual_metal.png")
plt.tight_layout()
plt.savefig(output_filename, dpi=300)
plt.close(fig)
