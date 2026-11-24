import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Robustly find the column name for residence time (handling potential whitespace variations)
res_col = None
for c in df.columns:
    if '체류시간' in str(c):
        res_col = c
        break

if res_col is None:
    raise KeyError("Column containing '체류시간' not found.")

# Ensure the column is numeric to avoid type errors in pd.cut
df[res_col] = pd.to_numeric(df[res_col], errors='coerce')

# Define bins: 0.5 s wide, from 2.5 to 7.0 s, left-closed
bins = np.arange(2.5, 7.5, 0.5)  # 2.5, 3.0, ..., 7.0 (edges)
labels = [f"{b:.1f}-{b+0.5:.1f}" for b in bins[:-1]] 
# Labels will be '2.5-3.0', '3.0-3.5', etc.

# Create bin column
df['체류시간_bin'] = pd.cut(df[res_col], bins=bins, labels=labels, right=False)

# Filter out rows where the bin is NaN (outside 2.5-7.0 range or non-numeric values)
df_filtered = df.dropna(subset=['체류시간_bin'])

# Pivot table: Mean CNT수율 by 체류시간_bin (rows) and 반응기 (columns)
pivot_table = df_filtered.pivot_table(
    index='체류시간_bin', 
    columns='반응기', 
    values='CNT수율 (g/g-cat)', 
    aggfunc='mean'
)

# Ensure all reactors are present as columns, even if missing in some bins
all_reactors = ['R1', 'R2', 'R3', 'R4']
for r in all_reactors:
    if r not in pivot_table.columns:
        pivot_table[r] = np.nan

# Reorder columns
pivot_table = pivot_table[all_reactors]

# Reorder index to match bin order
pivot_table = pivot_table.reindex(labels)

# Plot heatmap
fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(pivot_table.values, cmap='viridis', aspect='auto')

# Set ticks and labels
ax.set_xticks(np.arange(len(all_reactors)))
ax.set_yticks(np.arange(len(labels)))
ax.set_xticklabels(all_reactors)
ax.set_yticklabels(labels)

# Rotate x-axis labels for better readability
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# Add text annotations to each cell
for i in range(len(labels)):
    for j in range(len(all_reactors)):
        val = pivot_table.iloc[i, j]
        if not np.isnan(val):
            text_color = "white" if im.norm(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontsize=9)
        else:
            ax.text(j, i, "", ha="center", va="center", color="white", fontsize=9)

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("평균 CNT 수율 (g/g-cat)", rotation=-90, va="bottom")

# Labels and title
ax.set_xlabel("반응기")
ax.set_ylabel("체류시간 구간 (s)")
ax.set_title("체류시간별 평균 CNT 수율 히트맵")

# Tight layout
fig.tight_layout()

# Save plot
output_path = os.path.join(OUT_DIR, "heatmap_yield_by_residence_time_and_reactor.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()
