import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Load data
file_path = "data/doe_temp_h2.csv"
df = pd.read_csv(file_path, encoding='utf-8')

# Check column names to ensure they match the preview
# Expected columns: 실험번호, 실험순서, 2존온도(°C), H2/C2H4비, 반복, 수율(g/g-cat), 순도(%)
# We need '2존온도(°C)', '수율(g/g-cat)', and '순도(%)'

temp_col = '2존온도(°C)'
yield_col = '수율(g/g-cat)'
purity_col = '순도(%)'

# Get unique temperatures to create a colormap mapping
unique_temps = sorted(df[temp_col].unique())
colors = plt.cm.viridis(np.linspace(0, 1, len(unique_temps)))
color_map = dict(zip(unique_temps, colors))

# Create plot
fig, ax = plt.subplots(figsize=(10, 7))

for temp in unique_temps:
    subset = df[df[temp_col] == temp]
    ax.scatter(subset[yield_col], subset[purity_col], 
               color=color_map[temp], 
               label=f'{temp} °C',
               alpha=0.8,
               edgecolors='w',
               s=50)

ax.set_xlabel('수율 (g/g-cat)', fontsize=12)
ax.set_ylabel('순도 (%)', fontsize=12)
ax.set_title('DOE 실험: 수율과 순도의 관계 (2존 온도별 색상 구분)', fontsize=14)
ax.legend(title='2존 온도', loc='best')
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, 'doe_yield_vs_purity_by_temp.png')
plt.savefig(output_file, dpi=300)
plt.close()
