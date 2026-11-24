import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Ensure '주차' and '반응기' columns are present
if '주차' not in df.columns or '반응기' not in df.columns:
    raise ValueError("Required columns '주차' or '반응기' not found in the dataframe.")

# Convert '주차' to numeric to handle string/int mix issues safely
df['주차'] = pd.to_numeric(df['주차'], errors='coerce')

# Filter for weeks 1-26 (dropping NaNs if any conversion failed)
df = df.dropna(subset=['주차'])
df = df[df['주차'].between(1, 26)]
df['주차'] = df['주차'].astype(int)

# Create pivot table: rows = 반응기, cols = 주차, values = count of runs
heatmap_data = df.pivot_table(index='반응기', columns='주차', values='런ID', aggfunc='count')

# Reindex to ensure all reactors R1-R4 and weeks 1-26 are present, filling missing with 0
reactors = ['R1', 'R2', 'R3', 'R4']
weeks = list(range(1, 27))
heatmap_data = heatmap_data.reindex(index=reactors, columns=weeks).fillna(0).astype(int)

# Plot Heatmap
fig, ax = plt.subplots(figsize=(14, 5))
im = ax.imshow(heatmap_data.values, cmap='YlGnBu', aspect='auto')

# Set ticks and labels
ax.set_xticks(np.arange(len(weeks)))
ax.set_yticks(np.arange(len(reactors)))
ax.set_xticklabels(weeks)
ax.set_yticklabels(reactors)

plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# Loop over data dimensions and create text annotations
for i in range(len(reactors)):
    for j in range(len(weeks)):
        val = heatmap_data.iloc[i, j]
        
        # Determine text color for readability based on value relative to max
        vmax = heatmap_data.values.max()
        mid = vmax / 2
        
        if val > mid:
            color = "white"
        else:
            color = "black"
            
        ax.text(j, i, val, ha="center", va="center", color=color, fontsize=8)

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel("런 수", rotation=-90, va="bottom")

# Title and Labels
ax.set_title("반응기별 주간 런 수 히트맵 (주차 1~26)")
ax.set_xlabel("주차")
ax.set_ylabel("반응기")

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "heatmap_run_counts.png")
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Heatmap saved to {output_path}")
