import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Ensure all weeks 1-26 are present and reactors R1-R4 are in correct order
weeks_to_include = list(range(1, 27))
reactors_order = ['R1', 'R2', 'R3', 'R4']

# Create a full grid index to ensure missing combinations are handled
full_index = pd.MultiIndex.from_product([reactors_order, weeks_to_include], names=['반응기', '주차'])

# Find the exact column name for 가동시간
col_time_candidates = [c for c in df_runs.columns if "가동시간" in str(c)]
if not col_time_candidates:
    raise ValueError("Column containing '가동시간' not found")
col_time_name = col_time_candidates[0]

# Convert the time column to numeric to fix the TypeError (dtype->object issue)
# The error suggests the column might be read as object/string or contain non-numeric chars
df_runs[col_time_name] = pd.to_numeric(df_runs[col_time_name], errors='coerce')

# Calculate mean 가동시간 per reactor and week
grouped_mean = df_runs.groupby(['반응기', '주차'])[col_time_name].mean()

# Reindex to match the full grid (missing combinations will become NaN)
heatmap_data_series = grouped_mean.reindex(full_index)
heatmap_data = heatmap_data_series.unstack('주차')

# For plotting, we need to handle NaNs. imshow doesn't like NaNs unless masked.
data_values = heatmap_data.values.astype(float)
mask = np.isnan(data_values)

# Plotting
fig, ax = plt.subplots(figsize=(14, 6))

# Create heatmap
im = ax.imshow(np.ma.masked_where(mask, data_values), cmap='YlGnBu', aspect='auto')

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 가동시간 (h)', rotation=-90, va="bottom")

# Set ticks and labels
ax.set_xticks(np.arange(len(weeks_to_include)))
ax.set_yticks(np.arange(len(reactors_order)))
ax.set_xticklabels(weeks_to_include)
ax.set_yticklabels(reactors_order)

# Rotate x-axis labels for better readability if needed
ax.tick_params(axis='x', labelrotation=0)

# Set title and labels
ax.set_title('주간별 반응기 평균 가동시간 Heatmap')
ax.set_xlabel('주차')
ax.set_ylabel('반응기')

# Determine color scale limits for text contrast
valid_vals = data_values[~mask]
if len(valid_vals) > 0:
    min_val = valid_vals.min()
    max_val = valid_vals.max()
else:
    min_val = 0
    max_val = 1

# Annotate cells with values
for i in range(len(reactors_order)):
    for j in range(len(weeks_to_include)):
        val = data_values[i, j]
        if not np.isnan(val):
            # Normalize value to determine text color
            # If value is closer to max (darker background), use white; else black
            threshold = min_val + (max_val - min_val) / 2
            text_color = "white" if val > threshold else "black"
            
            # Format float to 1 decimal place
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=text_color, fontsize=8)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "heatmap_run_counts_mean_time.png")
plt.savefig(output_path, dpi=300)
plt.close()
