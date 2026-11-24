import pandas as pd
import matplotlib.pyplot as plt
import os

# Set font for Korean support
plt.rcParams["font.family"] = "Noto Sans CJK KR"

# Define output directory and create if it doesn't exist
OUT_DIR = "out/t1"
os.makedirs(OUT_DIR, exist_ok=True)

# Read the data file
file_path = "data/downtime.xlsx"
df = pd.read_excel(file_path, sheet_name="정지이력")

# Group by cause (원인) and sum downtime minutes (정지시간(분))
downtime_by_cause = df.groupby("원인")["정지시간(분)"].sum().sort_values(ascending=False)

# Create the bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(downtime_by_cause.index, downtime_by_cause.values, color='steelblue')

# Add labels and title
ax.set_xlabel("원인", fontsize=12)
ax.set_ylabel("총 정지 시간 (분)", fontsize=12)
ax.set_title("원인별 총 정지 시간", fontsize=14)

# Add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

# Adjust layout to prevent clipping
plt.tight_layout()

# Save the figure
output_filename = os.path.join(OUT_DIR, "downtime_by_cause.png")
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

# Close the plot to free memory
plt.close(fig)
