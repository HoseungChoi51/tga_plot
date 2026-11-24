import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df_runs = pd.read_excel(file_path, sheet_name='런로그')

# Prepare pivot table for heatmap
# Count runs per reactor and week
pivot_df = df_runs.pivot_table(index='반응기', columns='주차', values='런ID', aggfunc='count')

# Ensure all weeks 1-26 are present and reactors R1-R4 are in correct order
weeks_to_include = list(range(1, 27))
reactors_order = ['R1', 'R2', 'R3', 'R4']

# Reindex to make sure missing combinations show as NaN (which will be masked or shown as 0 if we fillna, but usually heatmap shows 0 if count is 0)
# It's better to reindex the original dataframe before pivoting or ensure the pivot has all columns.
# Let's create a full grid first
full_index = pd.MultiIndex.from_product([reactors_order, weeks_to_include], names=['반응기', '주차'])
full_df = df_runs.set_index(['반응기', '주차']).loc[:, '런ID'].groupby(level=[0, 1]).count().reindex(full_index, fill_value=0)
heatmap_data = full_df.unstack('주차')

# Plotting
fig, ax = plt.subplots(figsize=(14, 6))

# Create heatmap
im = ax.imshow(heatmap_data.values, cmap='YlGnBu', aspect='auto')

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('런 수', rotation=-90, va="bottom")

# Set ticks and labels
ax.set_xticks(np.arange(len(weeks_to_include)))
ax.set_yticks(np.arange(len(reactors_order)))
ax.set_xticklabels(weeks_to_include)
ax.set_yticklabels(reactors_order)

# Rotate x-axis labels for better readability if needed, though 1-26 might fit horizontally
ax.tick_params(axis='x', labelrotation=0)

# Set title and labels
ax.set_title('주간별 반응기 런 수 Heatmap')
ax.set_xlabel('주차')
ax.set_ylabel('반응기')

# Get the raw numpy array for reliable indexing
data_values = heatmap_data.values
max_val = data_values.max()

# Annotate cells with values
for i in range(len(reactors_order)):
    for j in range(len(weeks_to_include)):
        val = data_values[i, j]
        # Determine text color based on background intensity
        # If value is less than 60% of max, use black, otherwise white
        text_color = "black" if val < max_val * 0.6 else "white"
        ax.text(j, i, int(val), ha="center", va="center", color=text_color)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "heatmap_run_counts.png")
plt.savefig(output_path, dpi=300)
plt.close()
