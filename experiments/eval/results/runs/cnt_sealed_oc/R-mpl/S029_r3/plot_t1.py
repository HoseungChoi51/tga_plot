import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Clean column names if necessary (strip whitespace)
df.columns = df.columns.str.strip()

# Check for required columns
required_cols = ['2존온도(°C)', 'H2/C2H4비', '순도(%)']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in the dataset.")

# Convert numeric columns to appropriate types
df['2존온도(°C)'] = pd.to_numeric(df['2존온도(°C)'], errors='coerce')
df['H2/C2H4비'] = pd.to_numeric(df['H2/C2H4비'], errors='coerce')
df['순도(%)'] = pd.to_numeric(df['순도(%)'], errors='coerce')

# Drop rows with NaN values in key columns for pivot table stability
df_clean = df.dropna(subset=['2존온도(°C)', 'H2/C2H4비', '순도(%)'])

# Create pivot table: mean of 순도(%) by 2존온도 and H2/C2H4비
pivot_table = df_clean.pivot_table(
    index='2존온도(°C)',
    columns='H2/C2H4비',
    values='순도(%)',
    aggfunc='mean'
)

# Ensure index and columns are sorted for better visualization
pivot_table = pivot_table.sort_index().sort_index(axis=1)

# Plot heatmap using matplotlib
fig, ax = plt.subplots(figsize=(10, 8))

unique_temps = pivot_table.index.values
unique_ratios = pivot_table.columns.values
Z = pivot_table.values

# Prepare meshgrid for pcolormesh
# pcolormesh needs edges, but for a grid of cells where x/y are centers, 
# we can just pass the center coordinates if dimensions match, or calculate edges.
# Simpler approach for categorical-like numeric axes: use imshow with extent.
# However, pcolormesh is robust. Let's construct edge arrays.

# Calculate edges for x (ratios) and y (temps)
def get_edges(values):
    if len(values) < 2:
        return [values[0]-0.5, values[0]+0.5]
    midpoints = (values[:-1] + values[1:]) / 2
    edges = np.concatenate(([values[0] - (midpoints[0] - values[0])], midpoints, [values[-1] + (values[-1] - midpoints[-1])]))
    return edges

x_edges = get_edges(unique_ratios)
y_edges = get_edges(unique_temps)

# Z needs to be transposed because pcolormesh expects shape (len(y), len(x)) which matches our pivot (index=y, cols=x)
# Actually pivot_table values are already indexed by temps (rows) and ratios (cols).
# pcolormesh(X, Y, C) where X,Y are 2D grids.
X_grid, Y_grid = np.meshgrid(x_edges, y_edges)
# We need the cell values aligned with the centers. 
# Easiest way with pcolormesh: provide coordinates of corners.
# But since our unique_ratios/temps are discrete levels, let's use imshow which is often simpler for heatmaps of pivots.

im = ax.imshow(Z, interpolation='nearest', cmap='viridis', origin='lower',
               extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]])

# Add colorbar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('평균 순도 (%)', fontsize=12)

# Set titles and labels
ax.set_title('DOE 결과: 2존온도 × H2/C2H4비별 평균 순도 히트맵', fontsize=14)
ax.set_xlabel('H2/C2H4비', fontsize=12)
ax.set_ylabel('2존온도 (°C)', fontsize=12)

# Set ticks at the center of the cells
ax.set_xticks(unique_ratios)
ax.set_yticks(unique_temps)
ax.set_xticklabels([str(r) for r in unique_ratios])
ax.set_yticklabels([str(t) for t in unique_temps])

# Annotate cells with values
for i in range(len(unique_temps)):
    for j in range(len(unique_ratios)):
        val = Z[i, j]
        if not np.isnan(val):
            # Normalize value to determine text color
            norm_val = (val - im.get_clim()[0]) / (im.get_clim()[1] - im.get_clim()[0])
            text_color = 'white' if norm_val < 0.5 else 'black'
            
            ax.text(unique_ratios[j], unique_temps[i], f'{val:.2f}', 
                    ha='center', va='center', color=text_color, fontsize=9)

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, 'doe_purity_heatmap.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Heatmap saved to {output_path}")
