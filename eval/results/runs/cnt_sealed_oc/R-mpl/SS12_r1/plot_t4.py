import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and create if it doesn't exist
OUT_DIR = "out/t4"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# Ensure '일자' is datetime type to extract month
df['일자'] = pd.to_datetime(df['일자'])

# Extract Month (YYYY-MM format for clarity in labels)
df['월'] = df['일자'].dt.strftime('%Y-%m')

# Group by Month and Cause, summing downtime minutes
pivot_df = df.groupby(['월', '원인'])['정지시간(분)'].sum().unstack(fill_value=0)

# Sort months chronologically
pivot_df = pivot_df.sort_index()

# Normalize each month to 100%
pivot_normalized = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100

# Define colors for each cause for consistency
causes = pivot_normalized.columns.tolist()
colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac']

# Create the stacked bar chart
fig, ax = plt.subplots(figsize=(12, 7))

bottoms = [0] * len(pivot_normalized.index)

for i, cause in enumerate(causes):
    values = pivot_normalized[cause].values
    color = colors[i % len(colors)]
    bars = ax.bar(pivot_normalized.index, values, bottom=bottoms, label=cause, color=color, width=0.7)
    bottoms += values

# Add labels and title
ax.set_xlabel("월", fontsize=12)
ax.set_ylabel("정지 시간 비율 (%)", fontsize=12)
ax.set_title("월별 원인별 정지 시간 비율 (100% 정규화)", fontsize=14)

# Set y-axis limit to ensure full stack visibility
ax.set_ylim(0, 100)

# Move legend outside to the right
ax.legend(title="원인", loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0)

# Rotate x-axis labels if needed for better readability
plt.xticks(rotation=45, ha='right')

# Adjust layout to prevent clipping and make room for the legend
plt.tight_layout(rect=[0, 0, 0.85, 1])

# Save the figure as SVG
output_filename = os.path.join(OUT_DIR, "downtime_stacked_by_month_normalized.svg")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot to free memory
plt.close(fig)
