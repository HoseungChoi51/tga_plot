import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the Excel file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Clean column names to handle potential whitespace issues from Excel headers
df.columns = df.columns.str.strip()

# Identify the correct column names based on preview and cleaning
col_metal = [c for c in df.columns if '잔류금속' in c][0]
col_yield = [c for c in df.columns if 'CNT수율' in c][0]
col_lot = '촉매로트'
col_reactor = '반응기'

# Convert relevant columns to numeric to fix "dtype->object" error
# This handles cases where numbers might be stored as strings or have non-numeric entries
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')
df[col_yield] = pd.to_numeric(df[col_yield], errors='coerce')

# Drop rows where conversion failed (NaNs created by coerce) to ensure clean aggregation
df_clean = df.dropna(subset=[col_metal, col_yield])

# Aggregate per (촉매로트, 반응기): mean 잔류금속, mean CNT수율
group_cols = [col_lot, col_reactor]
agg_df = df_clean.groupby(group_cols).agg({
    col_metal: 'mean',
    col_yield: 'mean'
}).reset_index()

# Create plot
fig, ax = plt.subplots(figsize=(10, 8))

# Get unique catalyst lots for coloring and legend
unique_lots = agg_df[col_lot].unique()
colors = plt.cm.tab20(np.linspace(0, 1, len(unique_lots)))

for i, lot in enumerate(unique_lots):
    subset = agg_df[agg_df[col_lot] == lot]
    ax.scatter(
        subset[col_metal], 
        subset[col_yield], 
        color=colors[i], 
        label=f"{lot}", 
        s=100, 
        alpha=0.7,
        edgecolors='black',
        linewidths=0.5
    )

ax.set_xlabel(f'평균 {col_metal}', fontsize=12)
ax.set_ylabel(f'평균 {col_yield}', fontsize=12)
ax.set_title('촉매로트별 반응기 평균 잔류금속 vs CNT수율', fontsize=14)
ax.legend(title='촉매로트', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
output_path = os.path.join(OUT_DIR, "aggregate_residual_metal_vs_yield.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
