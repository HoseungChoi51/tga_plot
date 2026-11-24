import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t3"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the DOE data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Ensure numeric types for plotting and analysis
df['2존온도(°C)'] = pd.to_numeric(df['2존온도(°C)'])
df['수율(g/g-cat)'] = pd.to_numeric(df['수율(g/g-cat)'])
df['H2/C2H4비'] = pd.to_numeric(df['H2/C2H4비'])

# Pivot table to create heatmap matrix: Rows = H2 Ratio, Columns = Temperature, Values = Mean Yield
pivot_df = df.pivot_table(values='수율(g/g-cat)', index='H2/C2H4비', columns='2존온도(°C)', aggfunc='mean')

# Create the plot
fig, ax = plt.subplots(figsize=(10, 7))

# Draw heatmap using imshow or pcolormesh (imshow is often easier for categorical axes if handled right, 
# but here we have specific numerical ticks. We'll use imshow with extent or just let matplotlib handle indices and set ticks manually)
# Since index/columns are sorted numerically in pivot_table usually, we can use them directly.
im = ax.imshow(pivot_df.values, aspect='auto', cmap='YlOrRd')

# Set x-ticks (Temperature) and y-ticks (H2 Ratio)
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels([f"{int(t)}" for t in pivot_df.columns])
ax.set_yticklabels([f"{int(h)}" for h in pivot_df.index])

# Rotate x-axis labels if needed for better readability (though they are short)
plt.setp(ax.get_xticklabels(), rotation=0, ha="center", rotation_mode="anchor")

# Add text annotations inside each cell showing the mean yield value
for i in range(len(pivot_df.index)):
    for j in range(len(pivot_df.columns)):
        # Format the number to 2 decimal places
        text = ax.text(j, i, f"{pivot_df.iloc[i, j]:.2f}",
                       ha="center", va="center", color="black", fontsize=9)

# Labels and Title
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('H2/C2H4 비', fontsize=12)
ax.set_title('DOE 히트맵: 온도와 H2 비율에 따른 평균 CNT 수율', fontsize=14, fontweight='bold')

# Colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('평균 수율 (g/g-cat)', rotation=-90, va="bottom", fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "doe_yield_heatmap.png")
plt.savefig(output_path, dpi=300)
plt.close()
