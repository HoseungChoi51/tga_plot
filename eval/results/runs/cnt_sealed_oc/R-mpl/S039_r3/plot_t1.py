import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set Korean font
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read data
file_path = "data/run_log.xlsx"
df = pd.read_excel(file_path, sheet_name="런로그")

# Clean column names to handle potential whitespace or special character issues
df.columns = df.columns.str.strip()

# Identify the correct column name for Zone 2 Temperature
target_col = None
for col in df.columns:
    if '2존온도' in str(col):
        target_col = col
        break

if target_col is None:
    raise ValueError("Could not find '2존온도' column in the data.")

# Force conversion of the target column to numeric type to fix TypeError: agg function failed [how->mean,dtype->object]
df[target_col] = pd.to_numeric(df[target_col], errors='coerce')

# Filter and Group Data
# We want average 2-zone temperature
# Group by Reactor (column E '반응기') and Shift (column D '근무조')
grouped = df.groupby(['반응기', '근무조'])[target_col].mean().reset_index()

# Pivot to make plotting easier: Index=Reactor, Columns=Shift, Values=Mean Temp
pivot_df = grouped.pivot(index='반응기', columns='근무조', values=target_col)

# Ensure column order for consistent color assignment
shifts = ['주간', '야간']
existing_shifts = [s for s in shifts if s in pivot_df.columns]
if not existing_shifts:
    # Fallback if column names are weird, use all available
    existing_shifts = pivot_df.columns.tolist()
else:
    pivot_df = pivot_df[existing_shifts]

# Plotting
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(pivot_df.index))  # the label locations
width = 0.35  # the width of the bars

# Prepare colors based on number of shifts
colors = ['#4c72b0', '#dd8452', '#55a868', '#c44e52'] 

rects = []
for i, shift in enumerate(existing_shifts):
    offset = (i - (len(existing_shifts)-1)/2) * width
    rect = ax.bar(x + offset, pivot_df[shift], width, label=shift, color=colors[i % len(colors)])
    rects.append(rect)

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('평균 2존 온도 (°C)')
ax.set_title('반응기별 근무조에 따른 평균 2존 온도 비교')
ax.set_xticks(x)
ax.set_xticklabels(pivot_df.index)
ax.legend()

# Add value labels on top of bars
def add_value_labels(bars):
    for bar in bars:
        height = bar.get_height()
        # Check if height is valid before adding text
        if not np.isnan(height):
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)

for r in rects:
    add_value_labels(r)

# Set y-limit slightly higher than max value to make room for labels
max_val = pivot_df.max().max()
if not np.isnan(max_val):
    ax.set_ylim(0, max_val * 1.1)

plt.tight_layout()
save_path = os.path.join(OUT_DIR, "reactor_shift_zone2_temp.png")
plt.savefig(save_path, dpi=300)
plt.close()
