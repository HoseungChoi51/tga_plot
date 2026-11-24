import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# The column name in the actual dataframe is '가동시간' (without units), 
# based on the error message showing available columns.
target_col = '가동시간'

if target_col not in df.columns:
    raise ValueError(f"Required column '{target_col}' not found in the dataframe.")

# Ensure required columns are present
required_cols = ['주차', '반응기']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' not found in the dataframe.")

# Convert '주차' to numeric to handle string/int mix issues safely
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')

# Filter for weeks 1-26 and drop rows with invalid week or time data
df = df.dropna(subset=['주차'])
df = df[df['주차'].between(1, 26)]
df['주차'] = df['주차'].astype(int)

# Ensure the target column is numeric
df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
df = df.dropna(subset=[target_col])

# Create pivot table: rows = 반응기, cols = 주차, values = mean 가동시간 (h)
heatmap_data = df.pivot_table(index='반응기', columns='주차', values=target_col, aggfunc='mean')

# Reindex to ensure all reactors R1-R4 and weeks 1-26 are present, filling missing with NaN
reactors = ['R1', 'R2', 'R3', 'R4']
weeks = list(range(1, 27))
heatmap_data = heatmap_data.reindex(index=reactors, columns=weeks)

# Prepare data for plotting: convert NaNs to masked array so they don't appear colored
plot_data = heatmap_data.values
masked_data = np.ma.masked_invalid(plot_data)

# Plot Heatmap
fig, ax = plt.subplots(figsize=(14, 5))

# Use a colormap that handles masked values well (white for empty)
cmap = plt.get_cmap('YlGnBu').copy()
cmap.set_bad(color='white')

im = ax.imshow(masked_data, cmap=cmap, aspect='auto')

# Set ticks and labels
ax.set_xticks(np.arange(len(weeks)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels(weeks)
ax.set_yticklabels(reactors)

plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# Loop over data dimensions and create text annotations
vmax = np.nanmax(heatmap_data.values)
vmin = np.nanmin(heatmap_data.values)

for i in range(len(reactors)):
    for j in range(len(weeks)):
        val = heatmap_data.iloc[i, j]
        
        # Skip annotation if value is NaN (empty cell)
        if np.isnan(val):
            continue
            
        # Determine text color for readability based on value relative to max valid value
        # Normalize to 0-1 range for the colormap logic roughly
        if vmax == vmin:
            normalized_val = 0.5
        else:
            normalized_val = (val - vmin) / (vmax - vmin)
            
        # Threshold for switching text color from black to white
        # YlGnBu goes from light yellow (low) to dark blue (high). 
        # Darker colors need white text.
        if normalized_val > 0.6:
            color = "white"
        else:
            color = "black"
            
        # Format value to 1 decimal place
        ax.text(j, i, f"{val:.1f}", ha="center", va="center", color=color, fontsize=8)

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("평균 가동시간 (h)", rotation=-90, va="bottom")

# Title and Labels
ax.set_title("반응기별 주간 평균 가동시간 히트맵 (주차 1~26)")
ax.set_xlabel("주차")
ax.set_ylabel("반응기")

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "heatmap_mean_runtime.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Heatmap saved to {output_path}")
