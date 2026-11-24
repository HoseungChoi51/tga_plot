import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t2"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the DOE data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path)

# Ensure numeric types for plotting and analysis
df['2존온도(°C)'] = pd.to_numeric(df['2존온도(°C)'])
df['수율(g/g-cat)'] = pd.to_numeric(df['수율(g/g-cat)'])
df['H2/C2H4비'] = pd.to_numeric(df['H2/C2H4비'])

# Get unique H2 ratios to plot separate lines for each
h2_ratios = sorted(df['H2/C2H4비'].unique())

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot mean yield vs temperature for each H2 ratio separately
for h2 in h2_ratios:
    subset = df[df['H2/C2H4비'] == h2]
    # Group by temperature to calculate mean and std for this specific H2 ratio
    temp_groups = subset.groupby('2존온도(°C)')['수율(g/g-cat)']
    mean_yields = temp_groups.mean()
    std_yields = temp_groups.std()
    
    # Plot the line with markers
    ax.plot(mean_yields.index, mean_yields.values, 'o-', label=f'H2/C2H4 = {int(h2)}', linewidth=2, markersize=6)
    
    # Add error bars if standard deviation exists (handle NaNs from single points)
    if not np.isnan(std_yields).all():
        ax.errorbar(mean_yields.index, mean_yields.values, yerr=std_yields, fmt='none', ecolor='gray', capsize=5, alpha=0.7)

# Labels and Title
ax.set_xlabel('2존 온도 (°C)', fontsize=12)
ax.set_ylabel('수율 (g/g-cat)', fontsize=12)
ax.set_title('DOE 분석: H2 비율별 온도에 따른 CNT 수율 변화', fontsize=14, fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.7)

# Legend
ax.legend(loc='best', title='H2/C2H4 비', fontsize=10, title_fontsize=10)

# Adjust layout
plt.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "doe_yield_vs_temperature_by_h2.png")
plt.savefig(output_path, dpi=300)
plt.close()
