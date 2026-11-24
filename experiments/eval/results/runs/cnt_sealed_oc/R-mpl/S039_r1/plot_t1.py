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

# Identify columns to convert to numeric
numeric_cols = ['2존온도 (°C)', 'CNT수율 (g/g-cat)', '생산속도 (g/h)', '잔류금속 (wt%)', 
                '산화개시온도 (°C)', 'IG/ID', '체류시간 (s)', '외기습도 (%)', '가동시간 (h)',
                '1존온도 (°C)', '3존온도 (°C)', 'C2H4유량 (sccm)', 'H2유량 (sccm)', 'H2/C2H4비']

# Convert specified columns to numeric, coercing errors to NaN
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Filter out rows with missing critical data for the plot
# Note: The column name in the preview is '2존온도' but usually includes units in headers or might be just text.
# Based on previous error, it seems '2존온도' was read as object. Let's check actual header names from typical Excel structures.
# If the header is strictly '2존온도' without units in this specific file version causing issues, we handle it.
# However, looking at the preview: I 2존온도 (°C). So the column name likely contains "(°C)".
# But wait, in the first script I used '2존온도'. If that failed, maybe the column name is different or has whitespace.
# Let's try to find the column containing "2존" and "온도".

col_2zone = None
for c in df.columns:
    if "2존" in str(c) and "온도" in str(c):
        col_2zone = c
        break

if col_2zone is None:
    # Fallback if exact match fails, though unlikely given preview
    raise ValueError("Column for 2-zone temperature not found")

# Ensure the identified column is numeric
df[col_2zone] = pd.to_numeric(df[col_2zone], errors='coerce')

# Drop rows where key fields are null
df_plot = df.dropna(subset=['반응기', '근무조', col_2zone])

# Calculate mean 2-zone temperature by Reactor and Shift
grouped = df_plot.groupby(['반응기', '근무조'])[col_2zone].mean().reset_index()

# Pivot for easier plotting
pivot_df = grouped.pivot(index='반응기', columns='근무조', values=col_2zone)

# Ensure order of reactors is R1, R2, R3, R4
reactor_order = ['R1', 'R2', 'R3', 'R4']
# Only keep reactors present in pivot index
pivot_df = pivot_df.reindex([r for r in reactor_order if r in pivot_df.index])

# Define colors for shifts
colors = {'주간': '#1f77b4', '야간': '#ff7f0e'} # Blue for Day, Orange for Night

# Create bar chart
x = np.arange(len(pivot_df))  # label locations
width = 0.35  # width of bars

fig, ax = plt.subplots(figsize=(10, 6))

rects1 = ax.bar(x - width/2, pivot_df['주간'], width, label='주간', color=colors['주간'])
rects2 = ax.bar(x + width/2, pivot_df['야간'], width, label='야간', color=colors['야간'])

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('평균 2존 온도 (°C)', fontsize=12)
ax.set_title('반응기별 근무조 평균 2존 온도 비교', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(pivot_df.index, fontsize=12)
ax.legend(fontsize=12)

# Attach a text label above each bar in *rects*, displaying its height.
def add_labels(rects):
    for rect in rects:
        height = rect.get_height()
        if not np.isnan(height):
            ax.annotate(f'{height:.1f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

add_labels(rects1)
add_labels(rects2)

fig.tight_layout()

# Save figure
output_file = os.path.join(OUT_DIR, "shift_reactor_temp_comparison.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
