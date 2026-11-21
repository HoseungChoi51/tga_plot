import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t1"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the downtime data
file_path = "data/downtime.xlsx"
sheet_name = '정지이력'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Ensure column names are strings and clean them if necessary (though preview suggests they are fine)
# The preview shows: A 일자, B 시작시각, C 반응기, D 원인, E 정지시간(분), F 비고

# Count occurrences by cause ('원인')
cause_counts = df['원인'].value_counts()

# Sort by count descending for better visualization (optional but recommended)
cause_counts = cause_counts.sort_values(ascending=False)

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot bar chart
bars = ax.bar(cause_counts.index, cause_counts.values, color='skyblue', edgecolor='black')

# Add title and labels
ax.set_title('설비 정지 원인별 건수', fontsize=14)
ax.set_xlabel('정지 원인', fontsize=12)
ax.set_ylabel('건수', fontsize=12)

# Annotate bars with counts
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10)

# Adjust layout to prevent label clipping
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "downtime_cause_count.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Do not show the plot
plt.close()
