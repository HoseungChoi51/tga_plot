import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t4"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the downtime data
file_path = "data/downtime.xlsx"
sheet_name = '정지이력'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Ensure '정지시간(분)' is numeric
df['정지시간(분)'] = pd.to_numeric(df['정지시간(분)'], errors='coerce')

# Filter for R2 only
df_r2 = df[df['반응기'] == 'R2']

# Calculate sum of stoppage time by cause ('원인') for R2
cause_time_sum_r2 = df_r2.groupby('원인')['정지시간(분)'].sum()

# Sort values descending for better visualization in pie chart
cause_time_sum_r2 = cause_time_sum_r2.sort_values(ascending=False)

# Create the pie chart
fig, ax = plt.subplots(figsize=(10, 8))

# Plot pie chart with labels and autopct to show percentages
wedges, texts, autotexts = ax.pie(
    cause_time_sum_r2.values, 
    labels=cause_time_sum_r2.index, 
    autopct='%1.1f%%',
    startangle=90,
    colors=plt.cm.Paired.colors,
    textprops={'fontsize': 12}
)

# Make the percentage text bold for visibility
for autotext in autotexts:
    autotext.set_fontweight('bold')

# Add title indicating it's based on total stoppage time for R2
ax.set_title('R2 반응기 설비 정지 원인별 정지시간 합계 비중 (파이 차트)', fontsize=14)

# Equal aspect ratio ensures that pie is drawn as a circle
ax.axis('equal')

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "downtime_cause_time_pie_R2.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Do not show the plot
plt.close()
