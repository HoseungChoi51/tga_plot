import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = '런로그'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Identify the correct column name for residence time
residence_col = None
for col in df.columns:
    if '체류시간' in str(col):
        residence_col = col
        break

if residence_col is None:
    raise ValueError("Could not find '체류시간' column in the dataframe.")

# Convert to numeric, coercing errors to NaN
# This handles cases where cells might contain strings or mixed types causing the previous TypeError
df[residence_col] = pd.to_numeric(df[residence_col], errors='coerce')

# Define bin edges: 2.5 to 7.0 with step 0.5
edges = np.arange(2.5, 7.1, 0.5) # 2.5, 3.0, ..., 7.0
labels = [f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(len(edges)-1)]

# Bin the residence time data
# right=False means intervals are [low, high). 
df['체류시간_bin'] = pd.cut(df[residence_col], bins=edges, labels=labels, right=False)

# Drop rows where binning resulted in NaN (outside 2.5-7.0 range strictly, or due to edge cases/non-numeric)
df_valid = df.dropna(subset=['체류시간_bin'])

# Identify yield and reactor columns robustly
yield_col = None
for col in df_valid.columns:
    if 'CNT수율' in str(col):
        yield_col = col
        break

reactor_col = None
for col in df_valid.columns:
    if '반응기' in str(col):
        reactor_col = col
        break

if yield_col is None or reactor_col is None:
    raise ValueError("Could not find 'CNT수율' or '반응기' columns.")

# Ensure yield column is also numeric just in case
df_valid[yield_col] = pd.to_numeric(df_valid[yield_col], errors='coerce')

pivot_df = df_valid.pivot_table(index='체류시간_bin', columns=reactor_col, values=yield_col, aggfunc='mean')

# Reindex to ensure all bins are present even if some are empty (they will show as NaN/blank)
pivot_df = pivot_df.reindex(labels)

# Ensure reactors are sorted R1-R4 if they appear in arbitrary order
sorted_reactors = sorted(pivot_df.columns.tolist())
pivot_df = pivot_df[sorted_reactors]

# Prepare data for heatmap
data_for_heatmap = pivot_df.values.astype(float)

fig, ax = plt.subplots(figsize=(10, 8))

# Plot heatmap
im = ax.imshow(data_for_heatmap, cmap='YlOrRd', aspect='auto')

# Set ticks and labels
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels(pivot_df.columns)
ax.set_yticklabels(pivot_df.index)

# Rotate the tick labels and set their alignment.
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")
plt.setp(ax.get_yticklabels(), rotation=0, ha="right", rotation_mode="anchor")

# Loop over data dimensions and create text annotations.
for i in range(len(pivot_df.index)):
    for j in range(len(pivot_df.columns)):
        val = data_for_heatmap[i, j]
        if not np.isnan(val):
            # Text color white if value is high (dark background), black otherwise
            # Determine threshold based on vmin/vmax or normalized value
            norm_val = (val - im.norm.vmin) / (im.norm.vmax - im.norm.vmin)
            color = "white" if norm_val > 0.6 else "black"
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=color, fontsize=9)

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("평균 CNT 수율 (g/g-cat)", rotation=-90, va="bottom", fontsize=12)

# Title and Labels
ax.set_title("반응기별 체류시간 구간 평균 CNT 수율", fontsize=14, pad=20)
ax.set_xlabel("반응기", fontsize=12)
ax.set_ylabel("체류시간 구간 (s)", fontsize=12)

plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "heatmap_yield_by_residence_time_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close()
