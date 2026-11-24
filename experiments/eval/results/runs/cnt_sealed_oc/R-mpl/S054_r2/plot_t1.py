import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

# Define output directory
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
sheet_name = "런로그"
df = pd.read_excel(file_path, sheet_name=sheet_name)

def get_col(df, target):
    # Try exact match first
    if target in df.columns:
        return target
    # Try contains (handles potential prefixes like 'E ', 'S ', etc.)
    matches = [c for c in df.columns if target in str(c)]
    if matches:
        return matches[0]
    raise KeyError(f"Column {target} not found")

col_reactor = get_col(df, "반응기")
col_metal = get_col(df, "잔류금속")
col_humidity = get_col(df, "외기습도")

# Ensure numeric types for humidity and metal to avoid comparison errors during binning
# The error suggests a type mismatch or string presence. We force conversion to float.
df[col_humidity] = pd.to_numeric(df[col_humidity], errors='coerce')
df[col_metal] = pd.to_numeric(df[col_metal], errors='coerce')

# Drop rows where these critical columns are NaN after conversion
df_valid = df.dropna(subset=[col_humidity, col_metal])

# Create Humidity Bands
# <60, 60-75, >=75
bins = [-np.inf, 60, 75, np.inf]
labels = ["< 60%", "60–75%", "≥ 75%"]

# Use pd.cut. right=False means intervals are [a, b). 
# To match "< 60", "60-75", ">= 75":
# Band 1: x < 60 -> (-inf, 60) with right=False? No, standard cut uses right=True by default.
# If right=True: bins are (a, b]. 
# We want: 
# Group 1: < 60. This is not naturally handled by inclusive/exclusive cuts easily without adjusting bins/labels.
# Let's use right=False so intervals are [min, max).
# Bin edges: -inf, 60, 75, inf.
# Interval 1: [-inf, 60) -> Covers < 60. Label: "< 60%"
# Interval 2: [60, 75) -> Covers 60 <= x < 75. But user said 60-75. Usually implies inclusive upper or exclusive upper. 
# User request: "60–75". Given the next is "≥ 75", the boundary at 75 must go to the last group.
# So: 
# G1: x < 60
# G2: 60 <= x < 75
# G3: x >= 75
# Using right=False:
# Bins: [-inf, 60, 75, inf]
# Cuts: [-inf, 60), [60, 75), [75, inf]
# Labels correspond exactly to this logic.
df_valid['습도_구간'] = pd.cut(df_valid[col_humidity], bins=bins, labels=labels, right=False)

# Filter out any remaining NaNs in the category column just in case
df_valid = df_valid.dropna(subset=['습도_구간'])

# Calculate Mean Residual Metal grouped by Reactor and Humidity Band
pivot_table = df_valid.groupby([col_reactor, '습도_구간'])[col_metal].mean().unstack('습도_구간')

# Ensure all reactors R1-R4 are present and ordered
reactors_order = ['R1', 'R2', 'R3', 'R4']
# Reindex to ensure order and presence. If a reactor/band combo is missing, it becomes NaN.
pivot_table = pivot_table.reindex(index=reactors_order, columns=labels)

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(reactors_order))  # label locations
width = 0.25  # width of bars

rects1 = ax.bar(x - width, pivot_table['< 60%'], width, label='< 60%', color='#FF9999')
rects2 = ax.bar(x, pivot_table['60–75%'], width, label='60–75%', color='#66b3ff')
rects3 = ax.bar(x + width, pivot_table['≥ 75%'], width, label='≥ 75%', color='#99ff99')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_xlabel('반응기')
ax.set_ylabel('평균 잔류금속 (wt%)')
ax.set_title('반응기별 외기습도에 따른 평균 잔류금속 비교')
ax.set_xticks(x)
ax.set_xticklabels(reactors_order)
ax.legend(title="외기습도 구간")

# Attach a text label above each bar displaying its mean
for rects in [rects1, rects2, rects3]:
    for rect in rects:
        height = rect.get_height()
        if not np.isnan(height):
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

fig.tight_layout()

# Save figure
output_path = os.path.join(OUT_DIR, "mean_residual_metal_by_reactor_and_humidity.png")
plt.savefig(output_path, dpi=300)
plt.close()
