import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name='런로그')

# Find columns dynamically to handle potential naming variations
cols = df.columns.tolist()

def find_col(keyword):
    for c in cols:
        if keyword in str(c):
            return c
    raise KeyError(f"Column containing '{keyword}' not found. Available: {cols}")

col_humidity = find_col('외기습도')
col_metal = find_col('잔류금속')
col_reactor = find_col('반응기')

# Convert humidity column to numeric, coercing errors to NaN
# This handles cases where the cell might be text or have unexpected formatting
df[col_humidity] = pd.to_numeric(df[col_humidity], errors='coerce')

# Define humidity bands
def get_humidity_band(val):
    if pd.isna(val):
        return 'Unknown'
    elif val < 60:
        return "<60 %"
    elif 60 <= val < 75:
        return "60–75 %"
    else:
        return "≥75 %"

df['습도 밴드'] = df[col_humidity].apply(get_humidity_band)

# Group by reactor and humidity band, calculate mean residual metal
grouped_data = df.groupby([col_reactor, '습도 밴드'])[col_metal].mean().reset_index()

# Pivot for easier plotting
pivot_df = grouped_data.pivot(index=col_reactor, columns='습도 밴드', values=col_metal)

# Ensure order of reactors and bands
reactors_order = ['R1', 'R2', 'R3', 'R4']
bands_order = ['<60 %', '60–75 %', '≥75 %']

# Reindex to ensure all combinations are present even if missing in data
# Only keep standard bands for plotting
if 'Unknown' in pivot_df.columns:
    pivot_df = pivot_df.drop(columns=['Unknown'])

pivot_df = pivot_df.reindex(index=reactors_order, columns=bands_order)

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

n_reactors = len(reactors_order)
n_bands = len(bands_order)
bar_width = 0.8 / n_bands
index = np.arange(n_reactors)

colors = ['#4c72b0', '#dd8452', '#55a868']

for i, band in enumerate(bands_order):
    # Fill NaN with 0 for plotting bars, but we won't label them if they are effectively missing/zero due to no data
    plot_values = pivot_df[band].fillna(0)
    
    bars = ax.bar(index + i * bar_width - (n_bands-1)*bar_width/2, 
                  plot_values, 
                  bar_width, 
                  label=band, 
                  color=colors[i])
    
    # Add text on top of bars
    for j, bar in enumerate(bars):
        height = bar.get_height()
        # Only add text if there is actual data (not filled zero from NaN)
        original_val = pivot_df.iloc[j][band]
        if not pd.isna(original_val) and height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{original_val:.2f}',
                    ha='center', va='bottom', fontsize=9)

ax.set_xlabel('반응기')
ax.set_ylabel('평균 잔류금속 (wt%)')
ax.set_title('반응기별 및 외기습도 구간별 평균 잔류금속 비교')
ax.set_xticks(index)
ax.set_xticklabels(reactors_order)
ax.legend(title='외기습도 (%)')
ax.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
output_filename = os.path.join(OUT_DIR, "residual_metal_by_reactor_and_humidity.png")
plt.savefig(output_filename, dpi=300)
plt.close()
