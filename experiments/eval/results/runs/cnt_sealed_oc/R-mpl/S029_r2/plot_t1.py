import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Load data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Clean column names just in case of extra spaces (though preview looks clean)
df.columns = df.columns.str.strip()

# Identify columns based on preview description
col_temp = '2존온도(°C)'
col_ratio = 'H2/C2H4비'
col_purity = '순도(%)'

# Check if columns exist
if col_temp not in df.columns or col_ratio not in df.columns or col_purity not in df.columns:
    raise ValueError(f"Expected columns '{col_temp}', '{col_ratio}', '{col_purity}' not found.")

# Calculate mean purity grouped by temperature and ratio
pivot_table = df.pivot_table(values=col_purity, 
                             index=col_temp, 
                             columns=col_ratio, 
                             aggfunc='mean')

# Prepare plot
fig, ax = plt.subplots(figsize=(10, 8))

# Create heatmap using matplotlib imshow
heatmap_data = pivot_table.values

# Plotting
im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto', interpolation='nearest')

# Set ticks and labels
ax.set_xticks(np.arange(len(pivot_table.columns)))
ax.set_yticks(np.arange(len(pivot_table.index)))
ax.set_xticklabels([str(x) for x in pivot_table.columns])
ax.set_yticklabels([str(x) for x in pivot_table.index])

ax.set_xlabel('H2/C2H4 비')
ax.set_ylabel('2존 온도 (°C)')
ax.set_title('DOE 결과: 2존온도 × H2/C2H4비 평균 순도(%) 히트맵')

# Add text annotations for each cell
for i in range(len(pivot_table.index)):
    for j in range(len(pivot_table.columns)):
        val = heatmap_data[i, j]
        if not np.isnan(val):
            # Determine text color based on background brightness
            threshold = (np.nanmax(heatmap_data) - np.nanmin(heatmap_data)) / 2 + np.nanmin(heatmap_data)
            color = 'white' if val > threshold else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=9)

# Add colorbar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('평균 순도 (%)')

plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, 'doe_purity_heatmap.png')
plt.savefig(output_path, dpi=300)
plt.close(fig)
