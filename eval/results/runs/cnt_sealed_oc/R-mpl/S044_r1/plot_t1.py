import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# Check required columns
required_cols = ['반응기', '원인']
if not all(col in df.columns for col in required_cols):
    raise ValueError(f"Missing columns. Available: {df.columns.tolist()}")

# Clean data: remove rows with missing reactor or cause
df_clean = df.dropna(subset=['반응기', '원인']).copy()

# Get unique reactors and causes for ordering
reactors = sorted(df_clean['반응기'].unique())
causes = sorted(df_clean['원인'].unique())

# Create pivot table: Count of occurrences per Reactor (rows) and Cause (columns)
pivot_count = pd.crosstab(df_clean['반응기'], df_clean['원인'])

# Reindex to ensure all reactors and causes are present even if count is 0
pivot_count = pivot_count.reindex(index=reactors, columns=causes, fill_value=0)

# Plotting as a heatmap-style table
fig, ax = plt.subplots(figsize=(10, 6))

# Use imshow for the heatmap background
im = ax.imshow(pivot_count.values, cmap='YlOrRd', aspect='auto')

# Set ticks and labels
ax.set_xticks(np.arange(len(causes)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels(causes, rotation=45, ha='right')
ax.set_yticklabels(reactors)

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('정지 횟수', rotation=-90, va="bottom", fontsize=12)

# Show values in cells
for i in range(len(reactors)):
    for j in range(len(causes)):
        val = pivot_count.iloc[i, j]
        # Choose text color based on background brightness
        # Normalizing value for simple contrast check against colormap range
        vmax = im.get_clim()[1]
        vmin = im.get_clim()[0]
        norm_val = (val - vmin) / (vmax - vmin + 1e-6)
        text_color = "white" if norm_val > 0.5 else "black"
        
        ax.text(j, i, int(val),
                ha="center", va="center", color=text_color, fontsize=12)

# Labels and Title
ax.set_title("반응기별 원인별 정지 횟수 분포", fontsize=16, pad=20)
ax.set_xlabel("정지 원인", fontsize=12)
ax.set_ylabel("반응기", fontsize=12)

# Remove spines for cleaner look
for edge, spine in ax.spines.items():
    spine.set_visible(False)

# Adjust layout
plt.tight_layout()

# Save plot
save_path = os.path.join(OUT_DIR, "downtime_heatmap.png")
plt.savefig(save_path, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plot saved to {save_path}")
