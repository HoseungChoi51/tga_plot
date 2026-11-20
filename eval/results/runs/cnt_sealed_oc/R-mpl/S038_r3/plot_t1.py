import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set font for Korean text support
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False  # To display minus sign correctly

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names: strip whitespace to handle potential hidden spaces in headers
df.columns = df.columns.str.strip()

# Identify the yield column dynamically or use the cleaned name
yield_col = None
for col in df.columns:
    if '수율' in col and 'CNT' in col:
        yield_col = col
        break

if yield_col is None:
    raise ValueError("Could not find CNT yield column. Available columns: " + str(df.columns.tolist()))

# Ensure numeric types for plotting and calculation
df[yield_col] = pd.to_numeric(df[yield_col], errors='coerce')
df['반응기'] = df['반응기'].astype(str).str.strip()

# Filter out rows where yield or reactor is missing
df_plot = df.dropna(subset=[yield_col, '반응기'])

# Prepare data for boxplot: group by reactor
reactors = ['R1', 'R2', 'R3', 'R4']
yields_by_reactor = [df_plot[df_plot['반응기'] == r][yield_col].values for r in reactors]

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Boxplot with specific styling
# Note: In newer matplotlib versions, 'labels' was deprecated/removed in favor of 'tick_labels' or setting xticks separately.
# Using 'tick_labels' which is supported in recent versions (>=3.7), otherwise fallback logic might be needed.
# However, the safest way compatible with broad ranges is often just passing the data and then setting ticks.
bp = ax.boxplot(yields_by_reactor, 
                patch_artist=True, 
                medianprops=dict(color='black'))

# Manually set tick labels to ensure compatibility across matplotlib versions
ax.set_xticklabels(reactors)

# Color the boxes to distinguish reactors
colors = ['#8ecae6', '#219ebc', '#ffb703', '#fb8500']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add scatter points for individual runs to see distribution better
x_jitter = []
all_y_values = []
for i, r in enumerate(reactors):
    count = len(yields_by_reactor[i])
    if count > 0:
        x_jitter.extend([i + 1 + np.random.normal(0, 0.04) for _ in range(count)])
        all_y_values.extend(yields_by_reactor[i])

ax.scatter(x_jitter, all_y_values, alpha=0.5, s=10, color='gray', label='Individual Runs')

# Labels and Title
ax.set_ylabel('CNT 수율 (g/g-cat)', fontsize=12)
ax.set_xlabel('반응기', fontsize=12)
ax.set_title('반응기별 CNT 수율 분포 비교', fontsize=14)
ax.legend(loc='upper right')

# Grid
ax.yaxis.grid(True, linestyle='--', alpha=0.6)
ax.set_axisbelow(True)

# Calculate mean values to annotate on the plot
means = [np.mean(data) for data in yields_by_reactor if len(data) > 0]
for i, mean_val in enumerate(means):
    ax.text(i + 1, mean_val, f'평균: {mean_val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold')

# Adjust layout and save
plt.tight_layout()
save_path = os.path.join(OUT_DIR, "reactor_yield_comparison.png")
plt.savefig(save_path, dpi=300)
plt.close()
