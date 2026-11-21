import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define output directory
OUT_DIR = "out/t1"

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Read the DOE data (CSV file, so no sheet_name)
df = pd.read_csv("data/doe_temp_h2.csv")

# Define unique temperatures and colors
temperatures = sorted(df['2존온도(°C)'].unique())
colors = plt.cm.viridis(np.linspace(0, 1, len(temperatures)))

# Create figure
fig, ax = plt.subplots(figsize=(10, 7))

# Plot scatter for each temperature group
for temp, color in zip(temperatures, colors):
    subset = df[df['2존온도(°C)'] == temp]
    ax.scatter(subset['수율(g/g-cat)'], 
               subset['순도(%)'], 
               c=[color], 
               label=f'{temp} °C', 
               alpha=0.7, 
               edgecolors='w', 
               s=80)

# Labels and title
ax.set_xlabel('수율 (g/g-cat)', fontsize=12)
ax.set_ylabel('순도 (%)', fontsize=12)
ax.set_title('DOE 실험: 수율 vs 순도 (2존 온도별 색상 구분)', fontsize=14)
ax.legend(title='2존 온도', bbox_to_anchor=(1.05, 1), loc='upper left')

# Grid
ax.grid(True, linestyle='--', alpha=0.6)

# Tight layout to prevent label clipping
plt.tight_layout()

# Save plot
fig.savefig(f"{OUT_DIR}/doe_yield_vs_purity_by_temp.png", dpi=300, bbox_inches='tight')
plt.close(fig)
