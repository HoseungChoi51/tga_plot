import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean characters
plt.rcParams["font.family"] = "Noto Sans CJK KR"
plt.rcParams['axes.unicode_minus'] = False

# Define output directory
OUT_DIR = "out/t2"
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Read the downtime data
file_path = "data/downtime.xlsx"
sheet_name = '정지이력'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# Count occurrences by cause ('원인')
cause_counts = df['원인'].value_counts()

# Create the pie chart
fig, ax = plt.subplots(figsize=(8, 8))

# Plot pie chart with labels and autopct to show percentages
wedges, texts, autotexts = ax.pie(
    cause_counts.values, 
    labels=cause_counts.index, 
    autopct='%1.1f%%',
    startangle=90,
    colors=plt.cm.Paired.colors,
    textprops={'fontsize': 12}
)

# Make the percentage text white for better visibility on darker slices if needed, 
# but usually black is fine. Let's ensure they are readable.
for autotext in autotexts:
    autotext.set_color('black')
    autotext.set_fontweight('bold')

# Add title
ax.set_title('설비 정지 원인별 건수 (파이 차트)', fontsize=14)

# Equal aspect ratio ensures that pie is drawn as a circle
ax.axis('equal')

# Adjust layout
plt.tight_layout()

# Save figure
output_filename = os.path.join(OUT_DIR, "downtime_cause_pie.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Do not show the plot
plt.close()
