import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Load data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Identify columns dynamically to handle whitespace variations in headers
cols = df.columns.tolist()

col_metal = None
col_temp = None
col_reactor = None

for c in cols:
    if '잔류금속' in str(c):
        col_metal = c
    elif '산화개시온도' in str(c):
        col_temp = c
    elif '반응기' in str(c):
        col_reactor = c

if not (col_metal and col_temp and col_reactor):
    raise ValueError(f"Could not find required columns. Found: {cols}")

# Convert types
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')
df[col_temp] = pd.to_numeric(df[col_temp], errors='coerce')

# Drop rows with NaN values for plotting variables or reactor info
plot_df = df.dropna(subset=[col_metal, col_temp, col_reactor])

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 7))

# Unique reactors and colors/markers for distinction
reactors = sorted(plot_df[col_reactor].unique())
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
markers = ['o', 's', '^', 'D']

for i, reactor in enumerate(reactors):
    subset = plot_df[plot_df[col_reactor] == reactor]
    ax.scatter(
        subset[col_metal],
        subset[col_temp],
        c=colors[i % len(colors)],
        marker=markers[i % len(markers)],
        label=f'반응기 {reactor}',
        alpha=0.7,
        s=50,
        edgecolors='w',
        linewidth=0.5
    )

# Labels and Title using the detected column names for consistency
ax.set_xlabel(col_metal, fontsize=12)
ax.set_ylabel(col_temp, fontsize=12)
ax.set_title('반응기별 CNT 런 데이터: 잔류금속 vs 산화개시온도', fontsize=14)

# Legend
ax.legend(title='반응기 구분', loc='best', fontsize=10)

# Grid
ax.grid(True, linestyle='--', alpha=0.6)

# Tight layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "scatter_metal_vs_oxidation_temp_by_reactor.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
plt.close(fig)

print(f"Plot saved to {output_filename}")
