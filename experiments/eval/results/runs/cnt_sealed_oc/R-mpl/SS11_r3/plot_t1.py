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

# Read the DOE data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Ensure numeric types for plotting and analysis
df['2존온도(°C)'] = pd.to_numeric(df['2존온도(°C)'])
df['수율(g/g-cat)'] = pd.to_numeric(df['수율(g/g-cat)'])
df['H2/C2H4비'] = pd.to_numeric(df['H2/C2H4비'])

# Calculate mean yield per temperature to show the trend clearly
temp_groups = df.groupby('2존온도(°C)')['수율(g/g-cat)']
mean_yields = temp_groups.mean()
std_yields = temp_groups.std()

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot individual data points scattered by H2 ratio for context (optional but helpful in DOE)
# We will color code by H2 ratio to see if there's interaction, but the main request is Temperature vs Yield.
# To keep it clean and focused on the user's request "how yield changes with temperature", 
# we plot the mean line with error bars, and scatter points underneath.

scatter = ax.scatter(df['2존온도(°C)'], df['수율(g/g-cat)'], 
                     c=df['H2/C2H4비'], cmap='viridis', alpha=0.6, edgecolors='w', linewidth=0.5, label='개별 데이터')

# Plot the mean trend line
ax.plot(mean_yields.index, mean_yields.values, 'r-o', linewidth=2, markersize=8, label='평균 수율')

# Add error bars for standard deviation
ax.errorbar(mean_yields.index, mean_yields.values, yerr=std_yields, fmt='none', ecolor='gray', capsize=5, label='표준편차')

# Labels and Title
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('수율 (g/g-cat)', fontsize=12)
ax.set_title('DOE 분석: 2존 온도에 따른 CNT 수율 변화', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.7)

# Legend
legend = ax.legend(loc='best', fontsize=10)

# Color bar for H2 ratio
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('H2/C2H4 비', fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "doe_yield_vs_temperature.png")
plt.savefig(output_path, dpi=300)
plt.close()
