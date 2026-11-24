import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "out/t1"
FILE_PATH = "data/run_log.xlsx"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Read the data
df = pd.read_excel(FILE_PATH, sheet_name='런로그')

# 2. Preprocess data
# The error suggests the column '일자' contains string format like 'yyyy-mm-dd' which might be literal text 
# or standard ISO strings that failed parsing due to some edge case or header confusion.
# However, usually Excel dates read as datetime objects by default if formatted correctly in Excel.
# If they are strings, we need to parse them.
# Let's inspect/force conversion with a fallback for string formats.

def parse_date(x):
    if isinstance(x, str):
        try:
            return pd.to_datetime(x, format='%Y-%m-%d')
        except:
            return pd.to_datetime(x) # Let pandas infer
    return x

df['일자'] = df['일자'].apply(parse_date)

# Extract Month from Date (e.g., 2026-03)
df['월'] = df['일자'].dt.to_period('M').astype(str)

# Define pass condition: Grade 'A' or 'B' is usually considered pass.
def calculate_pass_rate(group):
    total_runs = len(group)
    if total_runs == 0:
        return 0.0
    pass_count = group['등급'].isin(['A', 'B']).sum()
    return (pass_count / total_runs) * 100

# Group by Reactor and Month, then apply calculation
pivot_data = df.groupby(['반응기', '월']).apply(calculate_pass_rate).reset_index(name='합격률')

# Pivot for Heatmap: Rows=Reactor, Cols=Month
heatmap_df = pivot_data.pivot(index='반응기', columns='월', values='합격률')

# Sort months chronologically
heatmap_df = heatmap_df.reindex(sorted(heatmap_df.columns), axis=1)

# Sort reactors R1-R4 naturally
reactor_order = ['R1', 'R2', 'R3', 'R4']
heatmap_df = heatmap_df.reindex(reactor_order)

# 3. Plotting
fig, ax = plt.subplots(figsize=(12, 6))

# Use imshow for heatmap
im = ax.imshow(heatmap_df.values, cmap='YlGnBu', aspect='auto', vmin=0, vmax=100)

# Set ticks and labels
ax.set_xticks(np.arange(len(heatmap_df.columns)))
ax.set_yticks(np.arange(len(heatmap_df.index)))
ax.set_xticklabels(heatmap_df.columns)
ax.set_yticklabels(heatmap_df.index)

# Rotate x-axis labels for readability
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Loop over data dimensions and create text annotations.
for i in range(len(heatmap_df.index)):
    for j in range(len(heatmap_df.columns)):
        val = heatmap_df.iloc[i, j]
        if not np.isnan(val):
            text = ax.text(j, i, f"{val:.1f}%",
                           ha="center", va="center", color="black")
        else:
            # Handle missing values if any
            text = ax.text(j, i, "-",
                           ha="center", va="center", color="white")

ax.set_title("반응기별 월간 합격률 (%) 히트맵")
ax.set_xlabel("월")
ax.set_ylabel("반응기")

fig.colorbar(im, ax=ax, label="합격률 (%)")

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/reactor_monthly_pass_rate_heatmap.png", dpi=300, bbox_inches='tight')
plt.close()
